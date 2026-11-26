# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the rawtoaces project.

"""Shared OCIO display processing for the GPU viewer and CPU file exports."""

from functools import lru_cache

import PyOpenColorIO as ocio


CONFIG_NAME = "studio-config-v2.2.0_aces-v1.3_ocio-v2.4"
DISPLAY = "sRGB - Display"
DEFAULT_VIEW = "Un-tone-mapped"


@lru_cache(maxsize=1)
def config():
    return ocio.Config.CreateFromBuiltinConfig(CONFIG_NAME)


def views():
    return list(config().getViews(DISPLAY))


def default_view():
    return DEFAULT_VIEW if DEFAULT_VIEW in views() else config().getDefaultView(DISPLAY)


class ColorPipeline:
    def __init__(self, view=None, gpu=False):
        self.view = view if view in views() else default_view()
        exposure = ocio.ExposureContrastTransform()
        exposure.makeExposureDynamic()
        group = ocio.GroupTransform()
        group.appendTransform(exposure)
        group.appendTransform(ocio.DisplayViewTransform(src="ACES2065-1", display=DISPLAY, view=self.view))
        processor = config().getProcessor(group)
        self.descriptor = None
        if gpu:
            self.processor = processor.getDefaultGPUProcessor()
            self.descriptor = ocio.GpuShaderDesc.CreateShaderDesc()
            self.descriptor.setLanguage(ocio.GPU_LANGUAGE_GLSL_1_3)
            self.descriptor.setFunctionName("RtaDisplay")
            self.descriptor.setResourcePrefix("rtaOcio_")
            self.processor.extractGpuShaderInfo(self.descriptor)
            # These pinned built-in display views are analytic. Never silently
            # ignore LUT resources if a future configuration changes that.
            if list(self.descriptor.getTextures()) or list(self.descriptor.get3DTextures()):
                raise RuntimeError("The selected OCIO view requires unsupported LUT resources.")
            self.uniforms = list(self.descriptor.getUniforms())
            self.properties = self.descriptor
        else:
            self.processor = processor.getDefaultCPUProcessor()
            self.properties = self.processor

    def set_exposure(self, exposure):
        self.properties.getDynamicProperty(ocio.DYNAMIC_PROPERTY_EXPOSURE).setDouble(float(exposure))

    def bind_uniforms(self, program):
        for name, uniform in self.uniforms:
            if uniform.type != ocio.UNIFORM_DOUBLE:
                raise RuntimeError("Unsupported OCIO dynamic uniform: " + name)
            program.setUniformValue1f(program.uniformLocation(name), uniform.getDouble())

    def apply(self, pixels, exposure=0.0):
        self.set_exposure(exposure)
        self.processor.applyRGBA(pixels)
        return pixels
