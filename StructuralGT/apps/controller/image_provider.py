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

    def convert_to_gray(self, image: np.ndarray) -> np.ndarray:
        """Convert an image to grayscale."""
        if image.dtype != np.uint8:
            image = (
                255 * (image - np.min(image)) / (np.ptp(image) + 1e-8)
            ).astype(np.uint8)
        if len(image.shape) == 2:
            return image  # Already grayscale
        if len(image.shape) == 3:
            if image.shape[2] == 3:
                return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            if image.shape[2] == 4:
                return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        raise ValueError("Unsupported image shape for grayscale conversion.")

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
            image = self.convert_to_gray(image)
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
        self.main_controller.update_image_model()

    def requestPixmap(self, img_id, size, requested_size) -> QPixmap:
        """Return the current pixmap."""
        return self.pixmap
