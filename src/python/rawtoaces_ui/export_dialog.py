# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the rawtoaces project.

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from .export import writable_formats


class ExportDialog(QDialog):
    def __init__(self, source, defaults, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save image as")
        self.resize(560, 240)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        folder = Path(defaults.get("directory", str(Path(source).parent)))
        self.path = QLineEdit(str(folder / (Path(source).stem + "." + defaults.get("suffix", "exr"))))
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        row_layout.addWidget(self.path, 1)
        row_layout.addWidget(browse)
        form.addRow("File", row)
        self.pixels = QComboBox()
        self.pixels.addItem("Source pixels", "source")
        self.pixels.addItem("Display-adjusted (current viewer controls)", "display")
        self.pixels.setCurrentIndex(max(0, self.pixels.findData(defaults.get("pixels", "source"))))
        form.addRow("Pixels", self.pixels)
        self.pixel_type = QComboBox()
        self.pixel_type.addItems(["auto", "uint8", "uint16", "half", "float"])
        self.pixel_type.setCurrentText(defaults.get("pixel_type", "auto"))
        form.addRow("Pixel type", self.pixel_type)
        self.compression = QLineEdit(defaults.get("compression", ""))
        self.compression.setPlaceholderText("Writer default, or an OpenImageIO compression name")
        form.addRow("Compression", self.compression)
        layout.addLayout(form)
        note = QLabel("Exports use full-resolution pixels. Display-adjusted exports apply the current sRGB OCIO view, exposure and channels. Integer formats quantise and clip values.")
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self):
        filters = ";;".join(name + " (" + " ".join("*." + ext for ext in extensions) + ")"
                            for name, extensions in writable_formats())
        filename, _ = QFileDialog.getSaveFileName(self, "Save image as", self.path.text(), filters)
        if filename:
            self.path.setText(filename)

    def _accept(self):
        path = Path(self.path.text()).expanduser()
        if not path.suffix or not path.parent.is_dir():
            QMessageBox.warning(self, "Output file", "Choose an existing directory and include a file extension.")
            return
        if path.exists() and QMessageBox.question(self, "Overwrite image?", "Replace " + str(path) + "?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        self.accept()

    def values(self):
        path = Path(self.path.text()).expanduser().resolve()
        return {"path": str(path), "directory": str(path.parent), "suffix": path.suffix.lstrip("."),
                "pixels": self.pixels.currentData(), "pixel_type": self.pixel_type.currentText(),
                "compression": self.compression.text().strip()}
