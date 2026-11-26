# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the rawtoaces project.

import json
import os
from pathlib import Path

from PySide6.QtCore import QSettings


def is_data_directory(path):
    return bool(path) and all((Path(path) / name).is_dir()
                              for name in ("camera", "illuminant", "cmf", "training"))


def initial_data_directory():
    """Only an explicit environment setting may prefill a new session."""
    path = os.environ.get("RAWTOACES_DATA_PATH", "").split(os.pathsep)[0]
    return str(Path(path).expanduser()) if path else ""


class SettingsStore:
    def __init__(self, filename=None):
        self.settings = (QSettings(str(filename), QSettings.Format.IniFormat) if filename
                         else QSettings("rawtoaces", "rawtoaces-ui"))

    def load(self):
        try:
            value = json.loads(self.settings.value("session", "{}"))
            return value if isinstance(value, dict) else {}
        except (ValueError, TypeError):
            return {}

    def save(self, state):
        self.settings.setValue("session", json.dumps(state))
        self.settings.sync()
