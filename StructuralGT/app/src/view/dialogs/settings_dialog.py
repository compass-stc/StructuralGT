"""Settings dialog for StructuralGT GUI."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QPushButton,
)
from PySide6.QtCore import Qt
from service.settings_service import SettingsService


class SettingsDialog(QDialog):
    """Settings dialog for StructuralGT GUI."""

    def __init__(self, settings_service: SettingsService, parent):
        """Initialize the settings dialog."""
        super().__init__(parent)
        self.settings_service = settings_service
        self.setWindowTitle("Settings")
        self.setMinimumSize(480, 360)
        self.resize(480, 360)
        theme = self.settings_service.get("theme")
        if theme == "light":
            self.setStyleSheet("background-color: #f0f0f0;")
        else:
            self.setStyleSheet("background-color: #232529;")

        layout = QVBoxLayout(self, alignment=Qt.AlignTop)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        theme_layout = QHBoxLayout(alignment=Qt.AlignLeft)
        theme_layout.setContentsMargins(5, 0, 5, 0)
        theme_layout.setSpacing(5)
        button_layout = QHBoxLayout(alignment=Qt.AlignCenter)
        button_layout.setSpacing(20)

        self.theme_label = QLabel("Theme", self)
        self.theme_label.setAlignment(Qt.AlignLeft)
        self.theme_label.setStyleSheet("font-weight: bold;")
        self.theme_light_button = QRadioButton("Light", self)
        self.theme_dark_button = QRadioButton("Dark", self)

        # Load current theme setting
        current_theme = self.settings_service.get("theme")
        if current_theme == "light":
            self.theme_light_button.setChecked(True)
        else:
            self.theme_dark_button.setChecked(True)

        self.save_button = QPushButton("Save", self)
        self.save_button.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.save_button.clicked.connect(self._on_save)
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        theme_layout.addWidget(self.theme_light_button)
        theme_layout.addWidget(self.theme_dark_button)
        layout.addWidget(self.theme_label)
        layout.addLayout(theme_layout)
        layout.addStretch(1)
        layout.addLayout(button_layout)

    def _on_save(self):
        if self.theme_light_button.isChecked():
            self.settings_service.set("theme", "light")
        elif self.theme_dark_button.isChecked():
            self.settings_service.set("theme", "dark")

        self.accept()
