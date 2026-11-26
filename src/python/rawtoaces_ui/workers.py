# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the rawtoaces project.

import json
import os
from pathlib import Path
import sys

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, Signal

from .jobs import validate_queue


class ConversionQueue(QObject):
    started = Signal(int, str)
    completed = Signal(int, bool)
    output = Signal(str)
    finished = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.busy = False
        self._process = None
        self._cancelled = False

    def start(self, filenames, options):
        if self.busy:
            raise RuntimeError("A conversion is already running.")
        validate_queue(filenames, options)
        self._filenames = list(filenames)
        self._options = options
        self._index = 0
        self._cancelled = False
        self.busy = True
        self._next()

    def cancel(self):
        """Finish the active file, then leave the remaining queue untouched."""
        self._cancelled = True

    def _next(self):
        if self._cancelled or self._index == len(self._filenames):
            self.busy = False
            self.finished.emit(self._cancelled)
            return
        import rawtoaces

        process = QProcess(self)
        self._process = process
        environment = QProcessEnvironment.systemEnvironment()
        paths = [str(Path(__file__).resolve().parent.parent),
                 str(Path(rawtoaces.__file__).resolve().parent)]
        if environment.contains("PYTHONPATH"):
            paths.append(environment.value("PYTHONPATH"))
        environment.insert("PYTHONPATH", os.pathsep.join(paths))
        process.setProcessEnvironment(environment)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.readyReadStandardOutput.connect(lambda: self._read(process))
        process.finished.connect(
            lambda code, status: self._done(
                process, code == 0 and status == QProcess.ExitStatus.NormalExit))
        process.errorOccurred.connect(lambda error: self._error(process, error))
        self.started.emit(self._index, self._filenames[self._index])
        process.start(sys.executable, ["-u", "-m", "rawtoaces_ui.worker"])
        request = {"filename": self._filenames[self._index], "options": self._options.to_dict()}
        process.write(json.dumps(request).encode("utf-8"))
        process.closeWriteChannel()

    def _read(self, process):
        text = bytes(process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if text:
            self.output.emit(text)

    def _error(self, process, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.output.emit(process.errorString() + "\n")
            self._done(process, False)

    def _done(self, process, success):
        if self._process is not process:
            return
        self._read(process)
        self._process = None
        process.deleteLater()
        self.completed.emit(self._index, success)
        self._index += 1
        QTimer.singleShot(0, self._next)
