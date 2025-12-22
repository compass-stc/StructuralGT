"""Main window for StructuralGT GUI."""

from StructuralGT import __version__
from view.resources import get_icon_path
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QGridLayout,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QMenuBar,
    QStatusBar,
    QLabel,
    QToolButton,
    QDialog,
    QApplication,
    QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QShortcut, QKeySequence
from view.widgets.welcome_widget import WelcomePage
from view.widgets.image_view_widget import ImageViewWidget
from view.widgets.graph_view_widget import GraphViewWidget
from view.widgets.ribbon_widget import RibbonBar
from view.widgets.analysis_widget import AnalysisWidget
from view.widgets.properties_widget import PropertiesWidget
from view.widgets.project_widget import ProjectWidget
from view.dialogs.about_dialog import AboutDialog
from view.dialogs.alert_dialog import show_alert
from view.dialogs.settings_dialog import SettingsDialog
from view.widgets.console_widget import ConsoleWidget
from view.monitor_window import MonitorWindow
from service.main_controller import MainController
from service.settings_service import SettingsService
from service.ui_service import UIService
from model.handler import HandlerRegistry


class MainWindow(QMainWindow):
    """Main window for StructuralGT GUI."""

    def __init__(
        self, controller: MainController, settings_service: SettingsService
    ):
        """Initialize the main window."""
        super().__init__()
        self.controller = controller
        self.settings_service = settings_service
        self.setWindowTitle("StructualGT")
        self.setGeometry(100, 100, 1080, 800)
        self.setMinimumSize(800, 600)

        # Menu Bar
        self.menu_bar = MenuBar(self)

        # Central Widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top layout for ribbon and content
        top_layout = QGridLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        # Ribbon
        self.ribbon_widget = RibbonBar(controller, self)

        # Panels
        self.left_panel = LeftPanel(controller, self)

        self.right_panel = RightPanel(controller, self)

        # Splitter
        splitter = QSplitter(Qt.Horizontal, central_widget)
        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([300, 780])

        top_layout.addWidget(self.ribbon_widget, 0, 0, 1, 2)
        top_layout.addWidget(splitter, 1, 0, 1, 2)

        # Console widget
        self.console_widget = ConsoleWidget(self)
        self.console_widget.setMaximumHeight(300)
        self.console_widget.setMinimumHeight(150)

        # Monitor window
        self.monitor_window = MonitorWindow(self.controller, self)

        # Add to main layout
        top_widget = QWidget()
        top_widget.setLayout(top_layout)
        main_layout.addWidget(top_widget, 1)
        main_layout.addWidget(self.console_widget, 0)

        # Status Bar
        self.status_bar = StatusBar(main_window=self, parent=self)
        self.setStatusBar(self.status_bar)

        self._connect_signals()

        # Apply initial theme
        self._apply_theme()

        # Bind shortcuts
        self._bind_shortcuts()

    def _apply_theme(self):
        custom_styles = UIService.get_custom_styles()
        theme = self.settings_service.get("theme")
        stylesheet = UIService.load_theme(
            theme=theme, custom_styles=custom_styles
        )
        QApplication.instance().setStyleSheet(stylesheet)
        # Refresh icons after theme change
        self._refresh_all_ui(theme)

    def _bind_shortcuts(self):
        """Bind shortcuts to the application."""
        QShortcut(QKeySequence.Quit, self).activated.connect(
            QApplication.instance().quit
        )
        QShortcut(QKeySequence("Ctrl+J"), self).activated.connect(
            lambda: self.status_bar.console_button.click()
        )
        QShortcut(QKeySequence("Ctrl+B"), self).activated.connect(
            lambda: self._on_toggle_left_panel()
        )
        QShortcut(QKeySequence("Ctrl+="), self).activated.connect(
            lambda: self.right_panel.image_view.set_zoom(
                self.right_panel.image_view._zoom + 0.1
            )
        )
        QShortcut(QKeySequence("Ctrl+-"), self).activated.connect(
            lambda: self.right_panel.image_view.set_zoom(
                self.right_panel.image_view._zoom - 0.1
            )
        )
        QShortcut(QKeySequence("Left"), self).activated.connect(
            lambda: self.right_panel.image_view._on_prev_slice()
        )
        QShortcut(QKeySequence("Right"), self).activated.connect(
            lambda: self.right_panel.image_view._on_next_slice()
        )
        QShortcut(QKeySequence("Ctrl+1"), self).activated.connect(
            lambda: self.left_panel.tabs.setCurrentIndex(0)
        )
        QShortcut(QKeySequence("Ctrl+2"), self).activated.connect(
            lambda: self.left_panel.tabs.setCurrentIndex(1)
        )
        QShortcut(QKeySequence("Ctrl+3"), self).activated.connect(
            lambda: self.left_panel.tabs.setCurrentIndex(2)
        )

    def _refresh_all_ui(self, theme: str):
        """Refresh all UI elements in the application based on theme."""
        self.ribbon_widget.refresh_ui(theme)
        self.right_panel.image_view.refresh_ui(theme)
        self.status_bar.refresh_ui(theme)
        self.console_widget.refresh_ui(theme)

    def _connect_signals(self):
        # UI Signals
        self.ribbon_widget.toggle_panel_signal.connect(
            self._on_toggle_left_panel
        )
        self.ribbon_widget.change_view_signal.connect(self._on_change_view)
        self.ribbon_widget.refresh_signal.connect(self._on_refresh)
        self.right_panel.welcome_page.folder_selected_signal.connect(
            self.controller.add_network
        )
        self.right_panel.welcome_page.file_selected_signal.connect(
            self.controller.add_point_network
        )

        # Controller Signals
        self.controller.change_view_signal.connect(self._on_change_view)
        self.controller.alert_signal.connect(self._on_alert)
        self.controller.handler_changed_signal.connect(
            self.left_panel.project_widget.refresh
        )
        self.controller.handler_changed_signal.connect(
            self.right_panel.image_view.refresh
        )
        self.controller.binarize_finished_signal.connect(
            self._on_binarize_finished
        )
        self.controller.extract_graph_finished_signal.connect(
            self._on_extract_graph_finished
        )

    def _on_toggle_left_panel(self):
        """Toggle the visibility of the left panel."""
        if self.left_panel.isVisible():
            self.left_panel.hide()
        else:
            self.left_panel.show()

    def _on_change_view(self, view_name):
        """Change the view in the right panel based on the selected option."""
        if view_name == "Welcome Page":
            self.right_panel.welcome_page.show()
            self.right_panel.image_view.hide()
            self.right_panel.graph_view.hide()
            self.right_panel.graph_view.clear()
            self.ribbon_widget.refresh_button.setDisabled(True)
            self.ribbon_widget.extract_graph_button.setDisabled(True)
            self.ribbon_widget.combo_box.setDisabled(True)
        elif view_name == "Raw Image" or view_name == "Binarized Image":
            self.right_panel.image_view.show()
            self.right_panel.graph_view.hide()
            self.right_panel.welcome_page.hide()
            self.ribbon_widget.refresh_button.setDisabled(False)
            self.ribbon_widget.extract_graph_button.setDisabled(False)
            self.ribbon_widget.combo_box.setDisabled(False)
            if self.ribbon_widget.combo_box.currentText() != view_name:
                self.ribbon_widget.combo_box.setCurrentText(view_name)
            self.right_panel.image_view.set_display_type(view_name)
        elif view_name == "Extracted Graph":
            self.right_panel.graph_view.show()
            self.right_panel.image_view.hide()
            self.right_panel.welcome_page.hide()
            self.ribbon_widget.refresh_button.setDisabled(False)
            self.ribbon_widget.extract_graph_button.setDisabled(False)
            self.ribbon_widget.combo_box.setDisabled(False)
            if self.ribbon_widget.combo_box.currentText() != view_name:
                self.ribbon_widget.combo_box.setCurrentText(view_name)
        elif view_name == "Extracted Graph Only":
            self.right_panel.graph_view.show()
            self.right_panel.image_view.hide()
            self.right_panel.welcome_page.hide()
            self.ribbon_widget.refresh_button.setDisabled(False)
            self.ribbon_widget.extract_graph_button.setDisabled(False)
            self.ribbon_widget.combo_box.setCurrentText("Extracted Graph")
            self.ribbon_widget.combo_box.setDisabled(True)

    def _on_alert(self, title: str, message: str):
        """Show alert dialog."""
        show_alert(title, message, self)

    def _on_binarize_finished(self, success: bool):
        """Handle binarize task completion."""
        if success:
            # Refresh image view if showing binarized image
            if self.right_panel.image_view.isVisible():
                handler = self.controller.get_selected_handler()
                if (
                    handler
                    and handler["ui_properties"]["display_type"] == "Raw Image"
                ):
                    self._on_change_view("Binarized Image")
                if (
                    handler
                    and handler["ui_properties"]["display_type"]
                    == "Binarized Image"
                ):
                    self.right_panel.image_view.refresh()

    def _on_extract_graph_finished(self, pipeline):
        """Handle extract graph task completion."""
        if pipeline is not None:
            handler = self.controller.get_selected_handler()
            if (
                handler
                and handler["ui_properties"]["display_type"]
                == "Binarized Image"
            ):
                self._on_change_view("Extracted Graph")
            self.right_panel.graph_view.set_pipeline(pipeline)
        else:
            self.right_panel.graph_view.clear()

    def _on_refresh(self):
        # Refresh project widget
        self.left_panel.project_widget.refresh()
        # Refresh properties widget
        self.left_panel.properties_widget.refresh()
        # Refresh currently visible view
        if self.right_panel.image_view.isVisible():
            self.right_panel.image_view.refresh()
        elif self.right_panel.graph_view.isVisible():
            self.right_panel.graph_view.refresh()


class LeftPanel(QWidget):
    """Left panel for StructuralGT GUI."""

    def __init__(self, controller: MainController, main_window: MainWindow):
        """Initialize the left panel."""
        super().__init__()
        self.setMinimumWidth(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget(self)
        self.project_widget = ProjectWidget(controller, self)
        self.properties_widget = PropertiesWidget(controller, self)

        self.analysis_widget = AnalysisWidget(
            controller=controller, parent=self
        )
        analysis_scroll = QScrollArea(self)
        analysis_scroll.setWidget(self.analysis_widget)
        analysis_scroll.setWidgetResizable(True)
        analysis_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        analysis_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.tabs.addTab(self.project_widget, "Project")
        self.tabs.addTab(self.properties_widget, "Properties")
        self.tabs.addTab(analysis_scroll, "Analysis")

        layout.addWidget(self.tabs)


class RightPanel(QWidget):
    """Right panel for StructuralGT GUI."""

    def __init__(self, controller: MainController, main_window: MainWindow):
        """Initialize the right panel."""
        super().__init__()
        self.main_window = main_window
        self.setMinimumWidth(600)

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.welcome_page = WelcomePage(self)
        self.image_view = ImageViewWidget(controller, main_window, self)
        self.graph_view = GraphViewWidget(self, controller)
        layout.addWidget(self.welcome_page, 0, 0, Qt.AlignCenter)
        layout.addWidget(self.image_view, 0, 0)
        layout.addWidget(self.graph_view, 0, 0)


class MenuBar(QMenuBar):
    """Menu bar for StructuralGT GUI."""

    def __init__(self, parent):
        """Initialize the menu bar."""
        super().__init__(parent)

        # Help menu
        help_menu = self.addMenu("Help")

        # About action
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self._show_about_dialog)

    def _show_about_dialog(self):
        """Show the About dialog."""
        dialog = AboutDialog(parent=self)
        dialog.exec()


class StatusBar(QStatusBar):
    """Status bar for StructuralGT GUI."""

    def __init__(self, main_window: MainWindow, parent):
        """Initialize the status bar."""
        super().__init__(parent)
        self.main_window = main_window
        self.setFixedHeight(30)
        self.setContentsMargins(5, 0, 5, 0)

        theme = self.main_window.settings_service.get("theme")
        self.settings_button = QToolButton()
        self.settings_button.setIcon(
            QIcon(get_icon_path("settings.png", theme))
        )
        self.settings_button.setToolTip("Settings")
        self.settings_button.setStyleSheet("background-color: transparent;")
        self.settings_button.clicked.connect(self._on_settings_clicked)

        self.console_button = QToolButton()
        self.console_button.setIcon(QIcon(get_icon_path("console.png", theme)))
        self.console_button.setToolTip("Console")
        self.console_button.setStyleSheet("background-color: transparent;")
        self.console_button.clicked.connect(self._on_console_clicked)

        self.monitor_button = QToolButton()
        self.monitor_button.setIcon(QIcon(get_icon_path("monitor.png", theme)))
        self.monitor_button.setToolTip("Monitor")
        self.monitor_button.setStyleSheet("background-color: transparent;")
        self.monitor_button.clicked.connect(self._on_monitor_clicked)

        self.addWidget(self.settings_button)
        self.addWidget(self.console_button)
        self.addWidget(self.monitor_button)
        version_label = QLabel(f"StructuralGT v{__version__}")
        self.addPermanentWidget(version_label)

    def refresh_ui(self, theme: str):
        """Refresh the UI of the status bar."""
        self.settings_button.setIcon(
            QIcon(get_icon_path("settings.png", theme))
        )
        self.console_button.setIcon(QIcon(get_icon_path("console.png", theme)))
        self.monitor_button.setIcon(QIcon(get_icon_path("monitor.png", theme)))

    def _on_settings_clicked(self):
        dialog = SettingsDialog(
            settings_service=self.main_window.settings_service, parent=self
        )
        if dialog.exec() == QDialog.Accepted:
            self.main_window._apply_theme()

    def _on_console_clicked(self):
        if self.main_window:
            console = self.main_window.console_widget
            console.setVisible(not console.isVisible())

    def _on_monitor_clicked(self):
        if self.main_window:
            monitor = self.main_window.monitor_window
            monitor.setVisible(not monitor.isVisible())
