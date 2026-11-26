# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the rawtoaces project.

"""Core-profile OpenGL image inspection; the source pixels stay scene-linear."""

import numpy as np
import traceback
from shiboken6 import VoidPtr

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QPainter, QColor, QColorSpace, QSurfaceFormat, QVector2D
from PySide6.QtOpenGL import (
    QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram, QOpenGLTexture,
    QOpenGLVertexArrayObject,
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from .color_management import ColorPipeline, default_view


VERTEX_SHADER = """#version 330 core
layout(location = 0) in vec2 position;
layout(location = 1) in vec2 texcoord;
uniform vec2 imageScale;
uniform vec2 pan;
out vec2 uv;
void main() {
    uv = texcoord;
    gl_Position = vec4(position * imageScale + pan, 0.0, 1.0);
}
"""

FRAGMENT_SHADER = """
uniform sampler2D imageTexture;
uniform int channel;
in vec2 uv;
out vec4 fragment;
void main() {
    vec4 sampleValue = texture(imageTexture, uv);
    vec3 rgb = sampleValue.rgb;
    if (channel >= 1 && channel <= 3) rgb = vec3(rgb[channel - 1]);
    else if (channel == 4) rgb = vec3(sampleValue.a);
    else if (channel == 5) rgb = vec3(dot(rgb, vec3(0.34396645, 0.72816610, -0.07213255)));
    if (channel != 4) rgb = RtaDisplay(vec4(rgb, 1.0)).rgb;
    float checker = mod(floor(gl_FragCoord.x / 12.0) + floor(gl_FragCoord.y / 12.0), 2.0);
    vec3 background = vec3(mix(0.12, 0.19, checker));
    float alpha = channel == 0 ? clamp(sampleValue.a, 0.0, 1.0) : 1.0;
    fragment = vec4(mix(background, rgb, alpha), 1.0);
}
"""


def configure_surface_format():
    surface = QSurfaceFormat()
    surface.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
    surface.setVersion(3, 3)
    surface.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    surface.setDepthBufferSize(0)
    surface.setStencilBufferSize(0)
    surface.setColorSpace(QColorSpace(QColorSpace.NamedColorSpace.SRgb))
    QSurfaceFormat.setDefaultFormat(surface)


class ImageView(QOpenGLWidget):
    error = Signal(str)
    view_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 200)
        self.image = None
        self.exposure = 0.0
        self.channel = 0
        self.color_view = default_view()
        self._color_pipeline = None
        self._compiled_view = None
        self.zoom = 1.0
        self.fit_image = True
        self.pan = QPointF()
        self._drag = None
        self._program = None
        self._texture = None
        self._vertices = None
        self._vao = None
        self._pending_upload = False
        self.gl_error = ""
        self._render_failed = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_image(self, image):
        self.image = image
        self._pending_upload = True
        self.fit()
        self.update()

    def fit(self):
        self.fit_image = True
        self.zoom = 1.0
        self.pan = QPointF()
        self.update()
        self.view_changed.emit()

    def actual_size(self):
        self.fit_image = False
        self.zoom = 1.0
        self.pan = QPointF()
        self.update()
        self.view_changed.emit()

    def initializeGL(self):
        # Keep exceptions inside Qt virtual callbacks: some PySide builds cannot
        # safely propagate an exception from a native OpenGL paint callback.
        try:
            self._initialize_gl()
        except Exception:
            self._fail(traceback.format_exc())

    def _initialize_gl(self):
        self.gl_error = ""
        self._render_failed = False
        self.context().aboutToBeDestroyed.connect(self.cleanup)
        functions = self.context().functions()
        functions.initializeOpenGLFunctions()
        self._create_program()
        program = self._program
        if program is None:
            return
        self._vao = QOpenGLVertexArrayObject(self)
        self._vao.create()
        self._vao.bind()
        self._vertices = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        self._vertices.create()
        self._vertices.bind()
        # OIIO scanlines are top-to-bottom; flip the texture coordinates once.
        data = np.array([-1, -1, 0, 1, 1, -1, 1, 1,
                         -1, 1, 0, 0, 1, 1, 1, 0], dtype=np.float32).tobytes()
        self._vertices.allocate(data, len(data))
        program.bind()
        program.enableAttributeArray(0)
        program.enableAttributeArray(1)
        program.setAttributeBuffer(0, 0x1406, 0, 2, 16)
        program.setAttributeBuffer(1, 0x1406, 8, 2, 16)
        self._vao.release()
        self._vertices.release()
        program.release()
        self._pending_upload = self.image is not None

    def _create_program(self):
        pipeline = ColorPipeline(self.color_view, gpu=True)
        fragment = "#version 330 core\n" + pipeline.descriptor.getShaderText() + FRAGMENT_SHADER
        program = QOpenGLShaderProgram(self)
        for stage, source in [(QOpenGLShader.ShaderTypeBit.Vertex, VERTEX_SHADER),
                              (QOpenGLShader.ShaderTypeBit.Fragment, fragment)]:
            if not program.addShaderFromSourceCode(stage, source):
                self._fail(program.log())
                return
        if not program.link():
            self._fail(program.log())
            return
        if self._program:
            self._program.removeAllShaders()
            self._program.deleteLater()
        self._program = program
        self._color_pipeline = pipeline
        self._compiled_view = self.color_view

    def _fail(self, message):
        self.gl_error = "OpenGL image view unavailable: " + message
        self._render_failed = True
        self.error.emit(self.gl_error)

    def paintGL(self):
        try:
            self._paint_gl()
        except Exception:
            self._fail(traceback.format_exc())

    def _paint_gl(self):
        functions = self.context().functions()
        # The OCIO processor already returns display-encoded sRGB pixels.
        functions.glDisable(0x8DB9)  # GL_FRAMEBUFFER_SRGB: avoid double encoding.
        functions.glClearColor(0.075, 0.08, 0.09, 1.0)
        functions.glClear(0x4000)  # GL_COLOR_BUFFER_BIT
        if self._program and self._compiled_view != self.color_view:
            self._create_program()
        if self.image is not None and self._program and not self._render_failed:
            if self._pending_upload:
                if self._texture:
                    self._texture.destroy()
                texture = QOpenGLTexture(QOpenGLTexture.Target.Target2D)
                texture.setSize(self.image.pixels.shape[1], self.image.pixels.shape[0])
                texture.setFormat(QOpenGLTexture.TextureFormat.RGBA32F)
                texture.allocateStorage(QOpenGLTexture.PixelFormat.RGBA,
                                        QOpenGLTexture.PixelType.Float32)
                texture.setData(QOpenGLTexture.PixelFormat.RGBA,
                                QOpenGLTexture.PixelType.Float32,
                                VoidPtr(self.image.pixels))
                texture.setMinMagFilters(QOpenGLTexture.Filter.Linear, QOpenGLTexture.Filter.Linear)
                texture.setWrapMode(QOpenGLTexture.WrapMode.ClampToEdge)
                self._texture = texture
                self._pending_upload = False
            width = self.image.width * self.image.pixel_aspect
            height = self.image.height
            factor = (min(self.width() / width, self.height() / height) if self.fit_image
                      else 1.0 / self.devicePixelRatioF())
            program = self._program
            program.bind()
            self._vao.bind()
            self._texture.bind(0)
            program.setUniformValue1i(program.uniformLocation("imageTexture"), 0)
            program.setUniformValue("imageScale", QVector2D(width * factor * self.zoom / self.width(),
                                                            height * factor * self.zoom / self.height()))
            program.setUniformValue("pan", QVector2D(2 * self.pan.x() / self.width(),
                                                     -2 * self.pan.y() / self.height()))
            program.setUniformValue1i(program.uniformLocation("channel"), self.channel)
            self._color_pipeline.set_exposure(self.exposure)
            self._color_pipeline.bind_uniforms(program)
            functions.glDrawArrays(0x0005, 0, 4)  # GL_TRIANGLE_STRIP
            self._texture.release()
            self._vao.release()
            program.release()
        else:
            painter = QPainter(self)
            painter.setPen(QColor(180, 185, 195))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                             self.gl_error or "Convert an image or open an EXR to inspect it")
            painter.end()

    def wheelEvent(self, event):
        self.zoom = min(100.0, max(0.02, self.zoom * 1.2 ** (event.angleDelta().y() / 120)))
        self.update()
        self.view_changed.emit()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self._drag is not None:
            self.pan += event.position() - self._drag
            self._drag = event.position()
            self.update()
            self.view_changed.emit()

    def mouseReleaseEvent(self, event):
        self._drag = None
        self.unsetCursor()

    def mouseDoubleClickEvent(self, event):
        self.fit()

    def cleanup(self):
        self.makeCurrent()
        if self._texture:
            self._texture.destroy()
        if self._vertices:
            self._vertices.destroy()
        if self._vao:
            self._vao.destroy()
        self._texture = self._vertices = self._vao = self._program = None
        self.doneCurrent()
