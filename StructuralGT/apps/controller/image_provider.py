from __future__ import annotations
import logging

import cv2
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PIL import Image, ImageQt  # Import ImageQt for conversion
from PySide6.QtGui import QPixmap
from PySide6.QtQuick import QQuickImageProvider
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .main_controller import MainController


class ImageProvider(QQuickImageProvider):
    """Provides images to the QML view."""

    def __init__(self, main_controller: MainController):
        super().__init__(QQuickImageProvider.ImageType.Pixmap)
        self.pixmap = QPixmap()
        self.main_controller = main_controller
        self.main_controller.refreshImageSignal.connect(self.refresh)

    def refresh(self):
        """Refresh the image in the QML view."""
        image_view_ctrl = self.main_controller.image_view_ctrl
        display_info = image_view_ctrl.get_display_info()
        logging.info(f"Refreshing image with display info: {display_info}")

        if display_info["display_type"] == "":
            logging.warning("ImageProvider: No images available to display.")
            self.pixmap = QPixmap()
        elif display_info["display_type"] == "raw":
            image = image_view_ctrl.get_raw_image()
            self.pixmap = ImageQt.toqpixmap(Image.fromarray(image))
        elif display_info["display_type"] == "binarized":
            try:
                image = image_view_ctrl.get_binarized_image()
                self.pixmap = ImageQt.toqpixmap(Image.fromarray(image))
            except Exception as e:
                self.pixmap = QPixmap()
                self.main_controller.showAlertSignal.emit(
                    "Image Error",
                    "No binarized image available. Apply binarizer first."
                )
        elif display_info["display_type"] == "extracted":
            try:
                image = image_view_ctrl.get_extracted_graph_image()
                self.pixmap = ImageQt.toqpixmap(Image.fromarray(image))
            except Exception as e:
                self.pixmap = QPixmap()
                self.main_controller.showAlertSignal.emit(
                    "Image Error",
                    "No extracted graph image available. Apply graph extraction first."
                )
        self.main_controller.imageRefreshedSignal.emit()

    def requestPixmap(self, img_id, size, requested_size) -> QPixmap:
        """Return the current pixmap."""
        return self.pixmap
