# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the rawtoaces project.

"""Categorised editors for ImageConverter.Settings, using binding defaults."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
    QSpinBox, QToolButton, QVBoxLayout, QWidget,
    QSizePolicy,
)

from .jobs import ConversionOptions
from .export import writable_formats
from .settings import initial_data_directory, is_data_directory


class Category(QWidget):
    def __init__(self, title, expanded=True):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        self.toggle = QToolButton(text=title.replace("&", "&&"), checkable=True, checked=expanded)
        self.toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle.setIconSize(QSize(10, 10))
        self.toggle.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.toggle.setObjectName("propertyCategory")
        self.body = QFrame()
        self.form = QFormLayout(self.body)
        self.form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        layout.addWidget(self.toggle)
        layout.addWidget(self.body)
        self.toggle.toggled.connect(self._expand)
        self._expand(expanded)

    def _expand(self, expanded):
        self.toggle.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)
        self.body.setVisible(expanded)


class PropertyPanel(QScrollArea):
    changed = Signal()

    def __init__(self, rawtoaces, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setMinimumWidth(340)
        self.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget()
        self.layout = QVBoxLayout(body)
        self.setWidget(body)
        self.fields = {}
        self._getters = {}
        self._setters = {}
        self.categories = {}
        defaults = rawtoaces.ImageConverter.Settings()
        self.defaults = defaults

        form = self.category("Colour & white balance")
        self.combo(form, "White balance", "WB_method", ["Metadata", "Illuminant", "Box", "Custom"], defaults.WB_method.name)
        self.text(form, "Illuminant", "illuminant", defaults.illuminant, "e.g. D55 or 3200K")
        self.vector(form, "WB region · X Y W H", "WB_box", defaults.WB_box, integer=True)
        self.vector(form, "Custom WB · R G B G₂", "custom_WB", defaults.custom_WB)
        self.combo(form, "Matrix method", "matrix_method", ["Auto", "Spectral", "Metadata", "Adobe", "Custom"], defaults.matrix_method.name)
        self.vector(form, "Camera RGB → ACES AP0", "custom_matrix", defaults.custom_matrix)
        self.number(form, "Highlight headroom", "headroom", defaults.headroom, 0.001, 1000)
        self.number(form, "Pixel scale", "scale", defaults.scale, 0.001, 1000)
        self.text(form, "Camera make override", "custom_camera_make", "", "From image metadata")
        self.text(form, "Camera model override", "custom_camera_model", "", "From image metadata")

        form = self.category("RAW decoding", False)
        self.combo(form, "Demosaicing", "demosaic_algorithm", ["linear", "VNG", "PPG", "AHD", "DCB", "DHT", "AAHD"], defaults.demosaic_algorithm)
        for label, key in [("Half-size decode", "half_size"), ("Automatic brightness", "auto_bright")]:
            self.check(form, label, key, getattr(defaults, key))
        self.number(form, "Maximum threshold", "adjust_maximum_threshold", defaults.adjust_maximum_threshold, 0, 1)
        self.number(form, "Black level override", "black_level", defaults.black_level, -1, 1000000, True, "Metadata")
        self.number(form, "Saturation override", "saturation_level", defaults.saturation_level, -1, 1000000, True, "Metadata")
        self.combo(form, "Highlight recovery", "highlight_mode", [("Clip", 0), ("Unclip", 1), ("Blend", 2)] + [("Rebuild " + str(i), i) for i in range(3, 10)], defaults.highlight_mode)
        self.number(form, "Denoising threshold", "denoise_threshold", defaults.denoise_threshold, 0, 100000)
        self.vector(form, "Aberration scales · R B", "chromatic_aberration", defaults.chromatic_aberration)
        self.path(form, "Bad-pixel file", "bad_pixels_path", "", directory=False)

        form = self.category("Crop & orientation", False)
        self.combo(form, "Crop mode", "crop_mode", ["Off", "Soft", "Hard"], defaults.crop_mode.name)
        self.vector(form, "Crop · X Y W H", "crop_box", defaults.crop_box, integer=True)
        self.combo(form, "Orientation", "flip", [("From metadata", -1), ("None", 0)] + [("EXIF " + str(i), i) for i in range(1, 9)], defaults.flip)

        form = self.category("Lens correction", False)
        flags = QWidget()
        flag_layout = QVBoxLayout(flags)
        flag_layout.setContentsMargins(0, 0, 0, 0)
        self.lens_checks = {}
        for title, name in [("Distortion", "Distortion"), ("Chromatic aberration", "Aberration"), ("Vignetting", "Vignetting")]:
            check = QCheckBox(title)
            check.toggled.connect(self.changed)
            flag_layout.addWidget(check)
            self.lens_checks[name] = check
        form.addRow("Apply", flags)
        self._register("lens_correction_types", flags,
                       lambda: [key for key, check in self.lens_checks.items() if check.isChecked()],
                       lambda values: [check.setChecked(key in values) for key, check in self.lens_checks.items()])
        self.check(form, "Require a matching lens", "require_lens_correction", defaults.require_lens_correction)
        self.text(form, "Lens make override", "custom_lens_make", "", "From image metadata")
        self.text(form, "Lens model override", "custom_lens_model", "", "From image metadata")
        for label, key in [("Aperture override · f/", "custom_aperture"), ("Focal length override · mm", "custom_focal_length"), ("Focus distance override", "custom_focus_distance")]:
            self.number(form, label, key, getattr(defaults, key), 0, 1000000, automatic="Metadata")

        form = self.category("Output")
        self.path(form, "Output folder", "output_dir", "", placeholder="Beside each input")
        self.combo(form, "File format", "output_format", [(name + " (." + extensions[0] + ")", extensions[0]) for name, extensions in writable_formats()], "exr")
        self.combo(form, "Pixel type", "output_type", ["auto", "uint8", "uint16", "half", "float"], "auto")
        self.combo(form, "Output pixels", "output_pixels", [("Scene-linear ACES", "scene-linear"), ("Display-adjusted (viewer)", "display")], "scene-linear")
        self.fields["output_pixels"].setToolTip("Scene-linear ACES retains scene values where the format supports them. Display-adjusted uses the current viewer controls. Integer formats quantise and clip values.")
        self.combo(form, "Compression", "compression", [("None", "none")] + [(name.upper(), name) for name in ("rle", "zip", "zips", "piz", "pxr24", "b44", "b44a", "dwaa", "dwab", "htj2k256", "htj2k32")], defaults.compression or "none")
        compression = self.fields["compression"]
        compression.setEditable(True)
        compression.setToolTip("Choose an EXR method, or type a compression method supported by the selected OpenImageIO writer.")
        compression.editTextChanged.connect(self.changed)
        self._getters["compression"] = lambda: (compression.currentData()
            if compression.currentIndex() >= 0 and compression.currentText() == compression.itemText(compression.currentIndex())
            else compression.currentText().strip())
        def restore_compression(value):
            index = compression.findData(value)
            if index >= 0:
                compression.setCurrentIndex(index)
            else:
                compression.setEditText(value)
        self._setters["compression"] = restore_compression
        self.check(form, "Create output folders", "create_dirs", defaults.create_dirs)
        self.check(form, "Overwrite existing files", "overwrite", defaults.overwrite)

        form = self.category("Database & diagnostics")
        self.path(form, "Spectral data folder", "database_directories", initial_data_directory())
        self.data_status = QLabel()
        self.data_status.setWordWrap(True)
        form.addRow(self.data_status)
        for label, key in [("Disable ExifTool", "disable_exiftool"), ("Disable cache", "disable_cache"), ("Log timing", "use_timing"), ("Keep diagnostic attributes", "keep_diagnostic_attributes")]:
            self.check(form, label, key, getattr(defaults, key))
        self.number(form, "Verbosity", "verbosity", defaults.verbosity, 0, 3, integer=True)
        self.layout.addStretch()
        self.fields["WB_method"].currentIndexChanged.connect(self._update_modes)
        self.fields["matrix_method"].currentIndexChanged.connect(self._update_modes)
        self.fields["database_directories"].textChanged.connect(self._update_data_status)
        self._update_modes()
        self._update_data_status()

    def category(self, title, expanded=True):
        category = Category(title, expanded)
        self.categories[title] = category
        self.layout.addWidget(category)
        return category.form

    def _register(self, key, widget, getter, setter):
        self.fields[key] = widget
        self._getters[key] = getter
        self._setters[key] = setter

    def combo(self, form, label, key, choices, default):
        widget = QComboBox()
        for choice in choices:
            title, value = choice if isinstance(choice, tuple) else (choice, choice)
            widget.addItem(title, value)
        widget.setCurrentIndex(max(0, widget.findData(default)))
        widget.currentIndexChanged.connect(self.changed)
        self._register(key, widget, widget.currentData,
                       lambda value: widget.setCurrentIndex(max(0, widget.findData(value))))
        form.addRow(label, widget)

    def text(self, form, label, key, default, placeholder=""):
        widget = QLineEdit(default)
        widget.setPlaceholderText(placeholder)
        widget.textChanged.connect(self.changed)
        self._register(key, widget, lambda: widget.text().strip(), widget.setText)
        form.addRow(label, widget)
        return widget

    def path(self, form, label, key, default, directory=True, placeholder=""):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        edit = QLineEdit(default)
        edit.setPlaceholderText(placeholder)
        edit.textChanged.connect(self.changed)
        browse = QPushButton("…")
        browse.setFixedWidth(28)
        def choose():
            path = (QFileDialog.getExistingDirectory(self, label, edit.text()) if directory
                    else QFileDialog.getOpenFileName(self, label, edit.text())[0])
            if path:
                # Accept either the rawtoaces-data checkout or its data directory.
                from pathlib import Path
                if key == "database_directories" and is_data_directory(Path(path) / "data"):
                    path = str(Path(path) / "data")
                edit.setText(path)
        browse.clicked.connect(choose)
        layout.addWidget(edit, 1)
        layout.addWidget(browse)
        getter = (lambda: [edit.text().strip()] if edit.text().strip() else []) if key == "database_directories" else lambda: edit.text().strip()
        setter = (lambda value: edit.setText(value[0] if value else "")) if key == "database_directories" else edit.setText
        self._register(key, edit, getter, setter)
        form.addRow(label, row)

    def check(self, form, label, key, default):
        widget = QCheckBox()
        widget.setChecked(default)
        widget.toggled.connect(self.changed)
        self._register(key, widget, widget.isChecked, widget.setChecked)
        form.addRow(label, widget)

    def number(self, form, label, key, default, low, high, integer=False, automatic=""):
        widget = QSpinBox() if integer else QDoubleSpinBox()
        widget.setRange(low, high)
        if not integer:
            widget.setDecimals(4)
            widget.setSingleStep(0.1)
        if automatic:
            widget.setSpecialValueText(automatic)
        widget.setValue(default)
        widget.valueChanged.connect(self.changed)
        self._register(key, widget, widget.value, widget.setValue)
        form.addRow(label, widget)

    def vector(self, form, label, key, values, integer=False):
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        matrix = isinstance(values[0], (list, tuple))
        rows = values if matrix else [values]
        editors = []
        for y, row in enumerate(rows):
            editors.append([])
            for x, value in enumerate(row):
                editor = QSpinBox() if integer else QDoubleSpinBox()
                editor.setRange(0 if integer else -10000, 100000 if integer else 10000)
                if not integer:
                    editor.setDecimals(4)
                    editor.setSingleStep(0.01)
                editor.setValue(value)
                editor.setMinimumWidth(42)
                editor.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
                editor.valueChanged.connect(self.changed)
                layout.addWidget(editor, y, x)
                editors[-1].append(editor)
        def get():
            result = [[editor.value() for editor in row] for row in editors]
            return result if matrix else result[0]
        def set_value(value):
            rows = value if matrix else [value]
            for controls, row in zip(editors, rows):
                for editor, item in zip(controls, row):
                    editor.setValue(item)
        self._register(key, widget, get, set_value)
        form.addRow(label, widget)

    def _update_modes(self):
        mode = self._getters["WB_method"]()
        form = self.categories["Colour & white balance"].form
        for key, visible in [("illuminant", mode == "Illuminant"), ("WB_box", mode == "Box"),
                             ("custom_WB", mode == "Custom"),
                             ("custom_matrix", self._getters["matrix_method"]() == "Custom")]:
            form.setRowVisible(self.fields[key], visible)

    def _update_data_status(self):
        paths = self._getters["database_directories"]()
        valid = bool(paths) and is_data_directory(paths[0])
        self.data_status.setText("✓ Spectral data found" if valid else "Choose a data folder containing camera, illuminant, cmf and training.")

    def options(self):
        return ConversionOptions({key: getter() for key, getter in self._getters.items()})

    def restore(self, values):
        for key, value in values.items():
            if key in self._setters:
                try:
                    self._setters[key](value)
                except (TypeError, ValueError, IndexError):
                    pass
        self._update_modes()
        self._update_data_status()
