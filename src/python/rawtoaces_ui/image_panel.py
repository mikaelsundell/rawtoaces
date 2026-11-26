# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the rawtoaces project.

from pathlib import Path

from PySide6.QtCore import QObject, QPointF, QRunnable, QThreadPool, Signal
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFileDialog, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout, QWidget,
)

from .image_view import ImageView
from .preview import read_preview
from .export import export_image
from .color_management import CONFIG_NAME, DISPLAY, default_view, views


class LoadSignals(QObject):
    ready = Signal(int, object)
    failed = Signal(int, str)
    exported = Signal(str, bool)


class ExportImage(QRunnable):
    def __init__(self, source, options, display, signals):
        super().__init__()
        self.source, self.options, self.display, self.signals = source, options, display, signals

    def run(self):
        try:
            output = export_image(self.source, self.options["path"], self.options["pixel_type"],
                                  self.display if self.options["pixels"] == "display" else None,
                                  self.options["compression"], overwrite=True)
            self.signals.exported.emit("Saved: " + str(output), True)
        except Exception as error:
            self.signals.exported.emit("Export failed: " + str(error), False)


class LoadImage(QRunnable):
    def __init__(self, filename, request, signals):
        super().__init__()
        self.filename, self.request, self.signals = filename, request, signals

    def run(self):
        try:
            self.signals.ready.emit(self.request, read_preview(self.filename))
        except Exception as error:
            self.signals.failed.emit(self.request, str(error))


class ImagePanel(QWidget):
    changed = Signal()
    message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._request = 0
        self.filename = ""
        self.loaded_filename = ""
        self.display_encoded = False
        self.export_options = {}
        self._pending_navigation = None
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.export_pool = QThreadPool(self)
        self.export_pool.setMaxThreadCount(1)
        self.signals = LoadSignals(self)
        self.signals.ready.connect(self._loaded)
        self.signals.failed.connect(self._failed)
        self.signals.exported.connect(self._exported)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        toolbar = QHBoxLayout()
        open_image = QPushButton("Open EXR…")
        open_image.clicked.connect(self._open)
        toolbar.addWidget(open_image)
        self.save_button = QPushButton("Save as…")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self._save_as)
        toolbar.addWidget(self.save_button)
        self.info = QLabel("Image view")
        toolbar.addWidget(self.info, 1)
        self.view = ImageView()
        self.view.error.connect(self.message)
        self.view.view_changed.connect(self.changed)
        for title, callback in [("Fit", self.view.fit), ("1:1", self.view.actual_size)]:
            button = QPushButton(title)
            button.clicked.connect(callback)
            toolbar.addWidget(button)
        layout.addLayout(toolbar)
        layout.addWidget(self.view, 1)
        controls = QHBoxLayout()
        self.exposure = QDoubleSpinBox()
        self.exposure.setRange(-16, 16)
        self.exposure.setSingleStep(0.25)
        self.exposure.setSuffix(" stops")
        self.channels = QComboBox()
        self.channels.addItems(["RGB", "Red", "Green", "Blue", "Alpha", "Luminance"])
        self.view_selector = QComboBox()
        for view in views():
            self.view_selector.addItem("Raw (bypass)" if view == "Raw" else view + " (sRGB)", view)
        self.view_selector.setCurrentIndex(self.view_selector.findData(default_view()))
        self.view_selector.setToolTip(CONFIG_NAME + "\nACES2065-1 → " + DISPLAY)
        for label, control in [("Exposure", self.exposure), ("Channel", self.channels)]:
            controls.addWidget(QLabel(label))
            controls.addWidget(control)
        controls.addWidget(QLabel("View"))
        controls.addWidget(self.view_selector, 1)
        reset = QPushButton("Reset view")
        reset.clicked.connect(self.reset)
        controls.addWidget(reset)
        layout.addLayout(controls)
        note = QLabel("OCIO · ACES2065-1 → " + DISPLAY + " · drag to pan, scroll to zoom")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.exposure.valueChanged.connect(self._update)
        self.channels.currentIndexChanged.connect(self._update)
        self.view_selector.currentIndexChanged.connect(self._update)

    def _update(self):
        self.view.exposure = self.exposure.value()
        self.view.channel = self.channels.currentIndex()
        self.view.color_view = self.view_selector.currentData()
        self.view.update()
        self.changed.emit()

    def reset(self):
        self.exposure.setValue(0)
        self.channels.setCurrentIndex(0)
        self.view_selector.setCurrentIndex(self.view_selector.findData(default_view()))
        self.view.fit()

    def _open(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open converted image", "", "OpenEXR (*.exr);;Images (*)")
        if filename:
            self.load(filename)

    def load(self, filename, display_encoded=False):
        self._request += 1
        self.filename = str(filename)
        self.display_encoded = display_encoded
        self.info.setText("Loading " + Path(filename).name + "…")
        self.pool.clear()
        self.pool.start(LoadImage(filename, self._request, self.signals))

    def _loaded(self, request, image):
        if request != self._request:
            return
        self.view.set_image(image)
        self.display_encoded = self.display_encoded or image.display_encoded
        self.loaded_filename = self.filename
        self.save_button.setEnabled(True)
        if self.display_encoded and not self._pending_navigation:
            self.exposure.setValue(0)
            self.channels.setCurrentIndex(0)
            self.view_selector.setCurrentIndex(self.view_selector.findData("Raw"))
        if self._pending_navigation:
            self._restore_navigation(self._pending_navigation)
            self._pending_navigation = None
        self.info.setText(f"{Path(self.filename).name} · {image.width} × {image.height} · "
                          f"preview {image.pixels.shape[1]} × {image.pixels.shape[0]}")
        self.changed.emit()

    def _failed(self, request, error):
        if request == self._request:
            self.info.setText("Unable to load " + Path(self.filename).name)
            self.message.emit(error)

    def state(self):
        return {"exposure": self.exposure.value(),
                "channel": self.channels.currentIndex(), "view": self.view_selector.currentData(),
                "zoom": self.view.zoom,
                "fit": self.view.fit_image, "pan": [self.view.pan.x(), self.view.pan.y()],
                "export": self.export_options, "display_encoded": self.display_encoded}

    def restore(self, state):
        self.export_options = state.get("export", {})
        for name, control in [("exposure", self.exposure)]:
            if isinstance(state.get(name), (int, float)):
                control.setValue(state[name])
        for name, control in [("channel", self.channels)]:
            if isinstance(state.get(name), int) and 0 <= state[name] < control.count():
                control.setCurrentIndex(state[name])
        if state.get("view") in views():
            self.view_selector.setCurrentIndex(self.view_selector.findData(state["view"]))
        self._restore_navigation(state)
        self._pending_navigation = state

    def _restore_navigation(self, state):
        zoom = state.get("zoom", 1.0)
        if isinstance(zoom, (int, float)):
            self.view.zoom = max(0.02, min(100.0, zoom))
        self.view.fit_image = bool(state.get("fit", True))
        pan = state.get("pan", [0, 0])
        if isinstance(pan, list) and len(pan) == 2 and all(isinstance(x, (int, float)) for x in pan):
            self.view.pan = QPointF(*pan)
        self.view.update()

    def _save_as(self):
        from .export_dialog import ExportDialog
        dialog = ExportDialog(self.loaded_filename, self.export_options, self)
        if dialog.exec():
            self.export_options = dialog.values()
            self.save_button.setEnabled(False)
            self.export_pool.start(ExportImage(self.loaded_filename, self.export_options, self.state(), self.signals))
            self.changed.emit()

    def _exported(self, message, success):
        self.save_button.setEnabled(bool(self.loaded_filename))
        self.message.emit(message + "\n")

    def shutdown(self):
        self.pool.clear()
        self.pool.waitForDone()
        self.export_pool.waitForDone()
        if self.view.isValid():
            self.view.cleanup()
