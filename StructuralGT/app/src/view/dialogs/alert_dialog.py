"""Alert dialog for StructuralGT GUI."""

import re
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPlainTextEdit,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt


def _format_error_message(message: str) -> str:
    message = re.sub(r"\s+", " ", message).strip()
    return message


def show_alert(title: str, message: str, parent=None):
    """Show alert dialog."""
    formatted_message = _format_error_message(message)

    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setModal(True)
    dialog.setMinimumSize(240, 120)
    dialog.resize(320, 160)

    layout = QVBoxLayout(dialog)
    layout.setSpacing(5)
    layout.setContentsMargins(5, 5, 5, 5)

    message_text = QPlainTextEdit(formatted_message, dialog)
    message_text.setReadOnly(True)
    message_text.setMaximumHeight(400)
    message_text.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
    message_text.setVerticalScrollBarPolicy(
        Qt.ScrollBarPolicy.ScrollBarAsNeeded
    )
    message_text.setHorizontalScrollBarPolicy(
        Qt.ScrollBarPolicy.ScrollBarAsNeeded
    )
    layout.addWidget(message_text)

    button_box = QDialogButtonBox(QDialogButtonBox.Ok, dialog)
    button_box.accepted.connect(dialog.accept)
    layout.addWidget(button_box)

    dialog.exec()
