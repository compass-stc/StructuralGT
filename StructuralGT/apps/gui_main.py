"""Main entry point of StructuralGT GUI."""

import logging
import sys
import pathlib

from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication
from apps.controller.main_controller import MainController
from apps.controller.image_provider import ImageProvider

logging.basicConfig(level=logging.INFO)


class MainWindow(QObject):
    """Main application window class."""

    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.ui_engine = QQmlApplicationEngine()

        # Register Controller for Dynamic Updates
        main_controller = MainController(qml_app=self.app, qml_engine=self.ui_engine)
        # Register Image Provider
        self.image_provider = ImageProvider(main_controller)

        # Set Models in QML Context
        self.ui_engine.rootContext().setContextProperty(
            "mainController", main_controller
        )
        self.ui_engine.addImageProvider("imageProvider", self.image_provider)
        self.ui_engine.rootContext().setContextProperty(
            "imagePropsModel", main_controller.imagePropsModel
        )
        self.ui_engine.rootContext().setContextProperty(
            "graphPropsModel", main_controller.graphPropsModel
        )
        self.ui_engine.rootContext().setContextProperty(
            "imageListModel", main_controller.imageListModel
        )

        # Load UI
        qml_dir = pathlib.Path(__file__).parent
        qml_name = "view/MainWindow.qml"
        qml_path = qml_dir / qml_name
        self.ui_engine.load(qml_path)
        if not self.ui_engine.rootObjects():
            sys.exit(-1)


def pyside_app():
    """Initialize and run the PySide GUI application."""
    main_window = MainWindow()
    sys.exit(main_window.app.exec())


if __name__ == "__main__":
    # Run the PySide application
    pyside_app()
