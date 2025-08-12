# SPDX-License-Identifier: GNU GPL v3

"""
Pyside6 implementation of StructuralGT user interface.
"""

import os
import sys
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication

from .gui_mcw.controller import MainController
from .gui_mcw.image_provider import ImageProvider


class MainWindow(QObject):
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.ui_engine = QQmlApplicationEngine()

        # Register Controller for Dynamic Updates
        controller = MainController(qml_app=self.app, qml_engine=self.ui_engine)
        # Register Image Provider
        self.image_provider = ImageProvider(controller)

        # Set Models in QML Context
        self.ui_engine.rootContext().setContextProperty("mainController", controller)
        self.ui_engine.addImageProvider("imageProvider", self.image_provider)
        self.ui_engine.rootContext().setContextProperty("imagePropsModel", controller.imagePropsModel)
        self.ui_engine.rootContext().setContextProperty("graphPropsModel", controller.graphPropsModel)
        self.ui_engine.rootContext().setContextProperty("imageListModel", controller.imageListModel)

        # Load UI
        qml_dir = os.path.dirname(os.path.abspath(__file__))
        qml_name = 'sgt_qml/MainWindow.qml'
        qml_path = os.path.join(qml_dir, qml_name)
        self.ui_engine.load(qml_path)
        if not self.ui_engine.rootObjects():
            sys.exit(-1)

def pyside_app():
    """
    Initialize and run the PySide GUI application.
    Returns:

    """
    main_window = MainWindow()
    sys.exit(main_window.app.exec())

if __name__ == "__main__":
    # Run the PySide application
    pyside_app()