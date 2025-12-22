# app/view/dialogs/about_dialog.py
"""About dialog for StructuralGT GUI."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices


class AboutDialog(QDialog):
    """About dialog widget for StructuralGT GUI."""

    def __init__(self, parent):
        """Initialize the about dialog."""
        super().__init__(parent)
        self.setWindowTitle("About StructuralGT")
        self.setModal(True)
        self.setMinimumSize(360, 240)
        self.resize(550, 450)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        self.about_label = QLabel(self)
        self.about_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.about_label.setWordWrap(True)
        self.about_label.setTextFormat(Qt.RichText)
        self.about_label.setOpenExternalLinks(False)
        self.about_label.linkActivated.connect(self._on_link_activated)

        # Set about text content
        about_text = (
            "A software tool that allows graph theory analysis of nano-structures.<br/><br/>"  # noqa: E501
            "This is a modified version of StructuralGT initially proposed by Drew A. Vecchio.<br/>"  # noqa: E501
            "DOI: <a href='https://pubs.acs.org/doi/10.1021/acsnano.1c04711'>10.1021/acsnano.1c04711</a><br/>"  # noqa: E501
            "Documentation: <a href='https://structuralgt.readthedocs.io'>structuralgt.readthedocs.io</a><br/><br/>"  # noqa: E501
            "Contributors:<br/>"
            "1. Nicolas Kotov<br/>"
            "2. Dickson Owuor<br/>"
            "3. Alain Kadar<br/><br/>"
            "This version of GUI is developed by Haoxuan Zeng.<br/>"
            "GitHub: <a href='https://github.com/HaoxuanZeng/SGT_GUI'>github.com/HaoxuanZeng/SGT_GUI</a><br/><br/>"  # noqa: E501
            "Copyright (C) 2018-2025, The Regents of the University of Michigan.<br/>"  # noqa: E501
            "License: BSD 3-Clause License<br/>"
        )
        self.about_label.setText(about_text)

        layout.addWidget(self.about_label, stretch=1)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok, self)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

    def _on_link_activated(self, link: str):
        """Handle link activation."""
        QDesktopServices.openUrl(QUrl(link))
