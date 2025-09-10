"""Main entry point of StructuralGT GUI."""

import logging
import sys
import pathlib
import signal

from PySide6.QtCore import QObject, QTimer
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication
from apps.controller.main_controller import MainController
from apps.controller.image_provider import ImageProvider
from apps.controller.signal_controller import SIGNAL_CONTROLLER

logging.basicConfig(level=logging.INFO)


class MainWindow(QObject):
    """Main application window class."""

    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.ui_engine = QQmlApplicationEngine()

        # Register Controller for Dynamic Updates
        self.main_controller = MainController(
            qml_app=self.app, qml_engine=self.ui_engine
        )
        # Register Image Provider
        self.image_provider = ImageProvider(self.main_controller)

        # Connect application about to quit signal
        self.app.aboutToQuit.connect(self.cleanup)

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Set Models in QML Context
        self.ui_engine.rootContext().setContextProperty(
            "mainController", self.main_controller
        )
        self.ui_engine.rootContext().setContextProperty(
            "signalController", SIGNAL_CONTROLLER
        )
        self.ui_engine.addImageProvider("imageProvider", self.image_provider)
        self.ui_engine.rootContext().setContextProperty(
            "imagePropsModel", self.main_controller.imagePropsModel
        )
        self.ui_engine.rootContext().setContextProperty(
            "graphPropsModel", self.main_controller.graphPropsModel
        )
        self.ui_engine.rootContext().setContextProperty(
            "networkListModel", self.main_controller.networkListModel
        )

        # Load UI
        qml_dir = pathlib.Path(__file__).parent
        qml_name = "view/MainWindow.qml"
        qml_path = qml_dir / qml_name
        self.ui_engine.load(qml_path)
        if not self.ui_engine.rootObjects():
            sys.exit(-1)

    def cleanup(self):
        """Clean up resources when application is closing."""
        logging.info("Application is closing, cleaning up resources...")

        # Clean up main controller
        if hasattr(self, "main_controller"):
            self.main_controller.cleanup()

        # Clean up QML engine
        if hasattr(self, "ui_engine"):
            self.ui_engine.deleteLater()

        logging.info("Application cleanup completed")

    def _signal_handler(self, signal, frame):
        """Handle system signals for shutdown."""
        logging.info(f"Received signal {signal}, initiating shutdown...")
        self.cleanup()
        self.app.quit()


def pyside_app():
    """Initialize and run the PySide GUI application."""
    main_window = MainWindow()
    sys.exit(main_window.app.exec())


if __name__ == "__main__":
    # Run the PySide application
    pyside_app()
