"""PySide6 Application for StructualGT."""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from view.main_window import MainWindow
from view.resources import get_app_icon_path
from service.main_controller import MainController
from service.ui_service import UIService
from service.settings_service import SettingsService
from model.handler import HandlerRegistry
import sys
from pathlib import Path

app_dir = Path(__file__).parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load settings
    settings_service = SettingsService()

    custom_styles = UIService.get_custom_styles()
    theme = settings_service.get("theme")
    stylesheet = UIService.load_theme(theme=theme, custom_styles=custom_styles)
    app.setStyleSheet(stylesheet)
    app.setWindowIcon(QIcon(get_app_icon_path()))

    handler_registry = HandlerRegistry()
    controller = MainController(handler_registry)
    window = MainWindow(controller, settings_service=settings_service)
    window.show()

    def cleanup():
        """Clean up threads before exit."""
        controller.cleanup_threads()

    app.aboutToQuit.connect(cleanup)
    sys.exit(app.exec())
