# apps/view/widgets/welcome_page.py
"""Welcome page widget for StructuralGT GUI."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtGui import QFont
from view.dialogs.file_dialog import select_folder, select_file


class WelcomePage(QWidget):
    """Welcome page widget."""

    folder_selected_signal = Signal(str, int)
    file_selected_signal = Signal(str)

    def __init__(self, parent):
        """Initialize the welcome page widget."""
        super().__init__(parent)
        self.setVisible(True)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        # Welcome title
        welcome_label = QLabel("Welcome to Structural GT")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_font = QFont()
        welcome_font.setBold(True)
        welcome_font.setPointSize(24)
        welcome_label.setFont(welcome_font)

        # Quick Analysis
        quick_label = QLabel("Quick Analysis")
        quick_font = QFont()
        quick_font.setBold(True)
        quick_font.setPointSize(16)
        quick_label.setFont(quick_font)
        quick_label.setAlignment(Qt.AlignCenter)

        # Card container for buttons
        card_layout = QVBoxLayout()
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_widget = QWidget()
        card_widget.setLayout(card_layout)

        # Add 2D Image button
        button_2d = QPushButton("Add 2D Image")
        button_2d.clicked.connect(self._on_add_2d_image)

        # Add 3D Image button
        button_3d = QPushButton("Add 3D Image")
        button_3d.clicked.connect(self._on_add_3d_image)

        # Add Point Network button
        button_point = QPushButton("Add Point Network")
        button_point.clicked.connect(self._on_add_point_network)

        card_layout.addWidget(button_2d)
        card_layout.addWidget(button_3d)
        card_layout.addWidget(button_point)

        # Center the card
        card_container = QHBoxLayout()
        card_container.addStretch()
        card_container.addWidget(card_widget)
        card_container.addStretch()

        layout.addWidget(welcome_label)
        layout.addWidget(quick_label)
        layout.addLayout(card_container)
        layout.addStretch()

    def _on_add_2d_image(self):
        folder_path = select_folder(self)
        if folder_path:
            self.folder_selected_signal.emit(folder_path, 2)

    def _on_add_3d_image(self):
        folder_path = select_folder(self)
        if folder_path:
            self.folder_selected_signal.emit(folder_path, 3)

    def _on_add_point_network(self):
        file_path = select_file(self, "CSV Files (*.csv);;All Files (*)")
        if file_path:
            self.file_selected_signal.emit(file_path)
