"""Dimension selection dialog for StructuralGT GUI."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QPushButton,
)
from PySide6.QtCore import Qt


class DimensionDialog(QDialog):
    """Dialog for selecting image dimension (2D or 3D)."""

    def __init__(self, parent):
        """Initialize the dimension dialog."""
        super().__init__(parent)
        self.setWindowTitle("Select Dimension")
        self.setMinimumSize(300, 240)
        self.resize(300, 240)
        self.selected_dimension = 2

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Dimension selection
        dimension_label = QLabel("Select Dimension", self)
        dimension_label.setAlignment(Qt.AlignLeft)
        dimension_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(dimension_label)

        dimension_layout = QHBoxLayout()
        dimension_layout.setContentsMargins(5, 0, 5, 0)
        dimension_layout.setSpacing(10)

        self.radio_2d = QRadioButton("2D", self)
        self.radio_2d.setChecked(True)  # Default to 2D
        self.radio_3d = QRadioButton("3D", self)

        dimension_layout.addWidget(self.radio_2d)
        dimension_layout.addWidget(self.radio_3d)
        dimension_layout.addStretch()

        layout.addLayout(dimension_layout)

        # Warning area (empty space for future warning messages)
        warning_label = QLabel(
            "When specified a 2D network, if there are several suitable images in the given directory, StructuralGT will take the first image by default.",  # noqa: E501
            self,
        )
        warning_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: #666; min-height: 30px;")
        self.warning_label = warning_label
        layout.addWidget(warning_label)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()

        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self._on_ok)
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def _on_ok(self):
        """Handle OK button click."""
        if self.radio_2d.isChecked():
            self.selected_dimension = 2
        elif self.radio_3d.isChecked():
            self.selected_dimension = 3
        self.accept()

    def get_dimension(self) -> int:
        """Get selected dimension."""
        return self.selected_dimension
