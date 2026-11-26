# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the rawtoaces project.

from pathlib import Path

from PySide6.QtCore import QByteArray, Qt, QTimer, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QHeaderView, QLabel, QMainWindow,
    QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QSplitter, QTableWidget,
    QTableWidgetItem, QWidget,
)

from .image_panel import ImagePanel
from .jobs import output_path
from .properties import PropertyPanel
from .settings import SettingsStore, is_data_directory
from .workers import ConversionQueue


class DropQueue(QTableWidget):
    files_dropped = Signal(list)

    def __init__(self):
        super().__init__(0, 2)
        self.setHorizontalHeaderLabels(["RAW image · drop files or folders here", "Status"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)

    def dragEnterEvent(self, event):
        if any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        self.dragEnterEvent(event)

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self, rawtoaces, state_path=None):
        super().__init__()
        self.rawtoaces = rawtoaces
        self.store = SettingsStore(state_path)
        self.filenames = []
        self.outputs = {}
        self._close_when_finished = False
        self.setWindowTitle("rawtoaces · RAW to ACES")
        self.resize(1440, 920)
        self.setAcceptDrops(True)
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(400)
        self.save_timer.timeout.connect(self.save_state)
        self.queue = ConversionQueue(self)

        resources = Path(__file__).resolve().parent / "resources"
        loader = QUiLoader()
        root = loader.load(str(resources / "main_window.ui"), self)
        if root is None:
            raise RuntimeError(loader.errorString())
        self.setCentralWidget(root)
        self.setStyleSheet((resources / "application.qss").read_text(encoding="utf-8"))
        self.data_button = root.findChild(QPushButton, "dataButton")
        self.data_button.clicked.connect(self._choose_data)
        properties_host = root.findChild(QWidget, "propertiesHost")
        self.properties = PropertyPanel(rawtoaces, properties_host)
        properties_host.layout().addWidget(self.properties)
        self.properties.changed.connect(self.save_timer.start)
        self.properties.changed.connect(self._update_data_button)
        self._update_data_button()
        viewer_host = root.findChild(QWidget, "viewerHost")
        self.image_panel = ImagePanel(viewer_host)
        viewer_host.layout().addWidget(self.image_panel)
        self.image_panel.changed.connect(self.save_timer.start)
        self.image_panel.message.connect(self._log)
        self.files = DropQueue()
        root.findChild(QWidget, "queueHost").layout().addWidget(self.files)
        self.files.files_dropped.connect(self.add_paths)
        self.files.itemSelectionChanged.connect(self._selection_changed)
        self.file_buttons = root.findChild(QWidget, "fileButtons")
        for name, callback in [("addFilesButton", self._browse_files), ("addFolderButton", self._browse_folder),
                               ("removeButton", self._remove), ("clearButton", self._clear)]:
            root.findChild(QPushButton, name).clicked.connect(callback)
        self.selection_info = root.findChild(QLabel, "selectionInfo")
        self.selection_info.setTextFormat(Qt.TextFormat.PlainText)
        self.log = root.findChild(QPlainTextEdit, "conversionLog")
        self.vertical_split = root.findChild(QSplitter, "contentSplitter")
        self.vertical_split.setSizes([540, 200, 100])
        self.splitter = root.findChild(QSplitter, "mainSplitter")
        self.splitter.setSizes([1000, 420])
        self.progress = root.findChild(QProgressBar, "conversionProgress")
        self.progress.setFormat("Ready")
        self.status_label = root.findChild(QLabel, "statusLabel")
        self.stop_button = root.findChild(QPushButton, "stopButton")
        self.stop_button.clicked.connect(self._stop)
        self.convert_button = root.findChild(QPushButton, "convertButton")
        self.convert_button.clicked.connect(self.start_conversion)
        self.queue.started.connect(self._started)
        self.queue.completed.connect(self._completed)
        self.queue.output.connect(self._log)
        self.queue.finished.connect(self._finished)
        self.restore_state()
        self.convert_button.setEnabled(bool(self.filenames))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and not self.queue.busy:
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.add_paths([url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()])
        event.acceptProposedAction()

    def _browse_files(self):
        extensions = " ".join("*." + ext.lstrip(".") for ext in self.rawtoaces.ImageConverter().get_supported_formats())
        paths, _ = QFileDialog.getOpenFileNames(self, "Add RAW images", "", "RAW images (" + extensions + ");;All files (*)")
        self.add_paths(paths)

    def _browse_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Add RAW image folder")
        if path:
            self.add_paths([path])

    def _choose_data(self):
        paths = self.properties.options().parameters.get("database_directories", [])
        folder = QFileDialog.getExistingDirectory(self, "Choose spectral data folder", paths[0] if paths else "")
        if folder:
            if is_data_directory(Path(folder) / "data"):
                folder = str(Path(folder) / "data")
            self.properties._setters["database_directories"]([folder])

    def _update_data_button(self):
        paths = self.properties.options().parameters.get("database_directories", [])
        valid = bool(paths) and is_data_directory(paths[0])
        self.data_button.setText("Spectral data ✓ · change…" if valid else "Choose spectral data folder…")
        self.data_button.setToolTip(paths[0] if paths else "Choose the data directory from rawtoaces-data.")

    def add_paths(self, paths):
        if self.queue.busy:
            self.statusBar().showMessage("Finish or stop the current batch before changing the queue.", 5000)
            return
        additions = []
        supported = {ext.lower().lstrip(".") for ext in self.rawtoaces.ImageConverter().get_supported_formats()}
        for item in paths:
            path = Path(item).expanduser()
            if path.is_dir():
                additions.extend(name for batch in self.rawtoaces.collect_image_files([str(path.resolve())]) for name in batch)
            elif path.is_file() and path.suffix.lower() == ".exr":
                self.image_panel.load(str(path.resolve()))
            elif path.is_file() and path.suffix.lower().lstrip(".") in supported:
                additions.append(str(path.resolve()))
            else:
                self._log("Not a supported RAW image: " + str(path) + "\n")
        for filename in additions:
            filename = str(Path(filename).resolve())
            if filename in self.filenames:
                continue
            self.filenames.append(filename)
            row = self.files.rowCount()
            self.files.insertRow(row)
            name = QTableWidgetItem(Path(filename).name)
            name.setToolTip(filename)
            self.files.setItem(row, 0, name)
            self.files.setItem(row, 1, QTableWidgetItem("Queued"))
        self.convert_button.setEnabled(bool(self.filenames))
        if self.files.rowCount() and not self.files.selectedItems():
            self.files.selectRow(0)
        self.save_timer.start()

    def _remove(self):
        for row in sorted({index.row() for index in self.files.selectedIndexes()}, reverse=True):
            self.outputs.pop(self.filenames[row], None)
            del self.filenames[row]
            self.files.removeRow(row)
        self.convert_button.setEnabled(bool(self.filenames))
        self.save_timer.start()

    def _clear(self):
        self.files.setRowCount(0)
        self.filenames.clear()
        self.outputs.clear()
        self.convert_button.setEnabled(False)
        self.save_timer.start()

    def _selection_changed(self):
        row = self.files.currentRow()
        if not 0 <= row < len(self.filenames):
            return
        filename = self.filenames[row]
        self.selection_info.setText(Path(filename).name + " · camera, lens and orientation come from this file's metadata unless overridden.")
        converted = self.outputs.get(filename)
        if isinstance(converted, dict):
            path = converted.get("path", "")
            if path and Path(path).is_file():
                self.image_panel.load(path, display_encoded=converted.get("display", False))
        elif converted and Path(converted).is_file():
            self.image_panel.load(converted)

    def start_conversion(self):
        options = self.properties.options()
        options.parameters["display_settings"] = self.image_panel.state()
        paths = options.parameters.get("database_directories", [])
        if not paths or not is_data_directory(paths[0]):
            self.properties.categories["Database & diagnostics"].toggle.setChecked(True)
            self.properties.ensureWidgetVisible(self.properties.fields["database_directories"])
            QMessageBox.warning(self, "Spectral data folder", "Choose the data directory inside rawtoaces-data under Database & diagnostics.")
            return
        if options.parameters["WB_method"] == "Illuminant" and not options.parameters["illuminant"]:
            QMessageBox.warning(self, "Illuminant", "Specify an illuminant, for example D55 or 3200K.")
            return
        try:
            # Start validates the whole batch before touching an output file.
            self.queue.start(self.filenames, options)
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(self, "Cannot start conversion", str(error))
            return
        self._active_options = options
        self._successes = 0
        self.file_buttons.setEnabled(False)
        self.properties.setEnabled(False)
        self.convert_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress.setRange(0, len(self.filenames))
        self.progress.setValue(0)
        for row in range(self.files.rowCount()):
            self.files.item(row, 1).setText("Queued" if row else "Converting")
        self.save_state()

    def _started(self, row, filename):
        self.files.item(row, 1).setText("Converting")
        self.progress.setFormat(f"{row + 1} / {len(self.filenames)} · {Path(filename).name}")
        self.status_label.setText(f"Converting {row + 1} / {len(self.filenames)}")
        self._log("\nConverting: " + filename + "\n")

    def _completed(self, row, success):
        self.files.item(row, 1).setText("Converted" if success else "Failed")
        self.progress.setValue(row + 1)
        if success:
            self._successes += 1
            result = str(output_path(self.filenames[row], self._active_options.output_dir, self._active_options.output_format))
            display = self._active_options.parameters.get("output_pixels") == "display"
            self.outputs[self.filenames[row]] = {"path": result, "display": display}
            self.image_panel.load(result, display_encoded=display)
        else:
            self.outputs.pop(self.filenames[row], None)

    def _stop(self):
        self.queue.cancel()
        self.stop_button.setEnabled(False)
        self.statusBar().showMessage("Finishing the current image; remaining files will stay in the queue.")

    def _finished(self, cancelled):
        self.file_buttons.setEnabled(True)
        self.properties.setEnabled(True)
        self.convert_button.setEnabled(bool(self.filenames))
        self.stop_button.setEnabled(False)
        for row in range(self.files.rowCount()):
            if self.files.item(row, 1).text() == "Queued":
                self.files.item(row, 1).setText("Not run")
        self.progress.setFormat(("Stopped" if cancelled else "Finished") + f" · {self._successes} converted")
        self.status_label.setText(("Stopped" if cancelled else "Finished") + f" · {self._successes} converted")
        self.statusBar().clearMessage()
        self.save_state()
        if self._close_when_finished:
            self.close()

    def _log(self, text):
        self.log.moveCursor(QTextCursor.MoveOperation.End)
        self.log.insertPlainText(text)
        self.log.ensureCursorVisible()

    def save_state(self):
        self.store.save({"parameters": self.properties.options().to_dict(),
                         "viewer": self.image_panel.state(), "queue": self.filenames,
                         "outputs": self.outputs, "last_image": self.image_panel.loaded_filename,
                         "geometry": bytes(self.saveGeometry().toBase64()).decode("ascii"),
                         "splitter": self.splitter.sizes(), "vertical_split": self.vertical_split.sizes(),
                         "categories": {name: category.toggle.isChecked() for name, category in self.properties.categories.items()}})

    def restore_state(self):
        state = self.store.load()
        parameters = state.get("parameters", {})
        if isinstance(parameters, dict):
            self.properties.restore(parameters)
        self.image_panel.restore(state.get("viewer", {}))
        self.outputs = state.get("outputs", {}) if isinstance(state.get("outputs", {}), dict) else {}
        self.add_paths([path for path in state.get("queue", []) if isinstance(path, str) and Path(path).is_file()])
        if state.get("geometry"):
            self.restoreGeometry(QByteArray.fromBase64(state["geometry"].encode("ascii")))
        for key, widget in [("splitter", self.splitter), ("vertical_split", self.vertical_split)]:
            values = state.get(key)
            if isinstance(values, list) and len(values) == widget.count() and all(isinstance(value, int) and value >= 0 for value in values):
                widget.setSizes(values)
        for name, expanded in state.get("categories", {}).items():
            if name in self.properties.categories:
                self.properties.categories[name].toggle.setChecked(bool(expanded))
        last = state.get("last_image", "")
        if last and Path(last).is_file():
            self.image_panel.load(last, display_encoded=bool(state.get("viewer", {}).get("display_encoded", False)))

    def closeEvent(self, event):
        if self.queue.busy:
            self._close_when_finished = True
            self._stop()
            event.ignore()
            return
        self.image_panel.shutdown()
        self.save_timer.stop()
        self.save_state()
        event.accept()
