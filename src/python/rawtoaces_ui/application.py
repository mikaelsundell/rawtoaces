# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the rawtoaces project.

import sys


def main():
    from PySide6.QtWidgets import QApplication, QMessageBox
    from .image_view import configure_surface_format

    configure_surface_format()
    app = QApplication(sys.argv)
    app.setApplicationName("rawtoaces")
    app.setOrganizationName("rawtoaces")
    try:
        import rawtoaces
    except ImportError as error:
        QMessageBox.critical(
            None, "rawtoaces bindings unavailable",
            "Build the Python bindings with the same interpreter used for the UI.\n\n"
            + str(error),
        )
        return 1

    from .main_window import MainWindow

    window = MainWindow(rawtoaces)
    if len(sys.argv) > 1:
        window.add_paths(sys.argv[1:])
    window.show()
    return app.exec()
