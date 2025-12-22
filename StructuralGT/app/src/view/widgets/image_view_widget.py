"""Image view widget for StructuralGT GUI."""

import numpy as np
import cv2
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QCursor, QImage
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QToolButton,
    QScrollArea,
    QLabel,
    QSizePolicy,
    QLineEdit,
)
from service.main_controller import MainController
from view.resources import get_icon_path


class ImageViewWidget(QWidget):
    """Image view widget for StructuralGT GUI."""

    def __init__(self, controller: MainController, main_window, parent):
        """Initialize the image view widget."""
        super().__init__(parent)
        self.controller = controller
        self.main_window = main_window
        self.editable = False
        self.setVisible(False)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._current_display_type = (
            "Raw Image"  # "Raw Image", "Binarized Image"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(0)

        zoom_layout = QHBoxLayout()
        zoom_layout.setContentsMargins(5, 5, 5, 5)
        zoom_layout.setSpacing(5)

        theme = self.main_window.settings_service.get("theme")
        self.zoom_in_button = QToolButton()
        self.zoom_in_button.setIcon(QIcon(get_icon_path("zoom_in.png", theme)))
        self.zoom_in_button.setToolTip("Zoom In")
        self.zoom_in_button.setStyleSheet("background-color: transparent;")

        self.zoom_out_button = QToolButton()
        self.zoom_out_button.setIcon(
            QIcon(get_icon_path("zoom_out.png", theme))
        )
        self.zoom_out_button.setToolTip("Zoom Out")
        self.zoom_out_button.setStyleSheet("background-color: transparent;")

        zoom_layout.addWidget(self.zoom_in_button, alignment=Qt.AlignLeft)
        zoom_layout.addStretch(1)
        zoom_layout.addWidget(self.zoom_out_button, alignment=Qt.AlignRight)

        layout.addLayout(zoom_layout)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidgetResizable(False)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(
            QSizePolicy.Ignored, QSizePolicy.Ignored
        )

        self.scroll_area.setWidget(self.image_label)

        layout.addWidget(self.scroll_area, 1)

        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(5, 5, 5, 5)
        nav_layout.setSpacing(5)

        self.prev_button = QToolButton()
        self.prev_button.setIcon(QIcon(get_icon_path("previous.png", theme)))
        self.prev_button.setToolTip("Previous Slice")
        self.prev_button.setStyleSheet("background-color: transparent;")

        self.next_button = QToolButton()
        self.next_button.setIcon(QIcon(get_icon_path("next.png", theme)))
        self.next_button.setToolTip("Next Slice")
        self.next_button.setStyleSheet("background-color: transparent;")

        self.slice_label = QLabel("0 / 0")
        self.slice_label.setAlignment(Qt.AlignCenter)
        self.slice_label.setCursor(QCursor(Qt.IBeamCursor))
        self.slice_label.mousePressEvent = self._on_slice_label_clicked

        self.slice_input = QLineEdit()
        self.slice_input.setFixedSize(50, 24)
        self.slice_input.setAlignment(Qt.AlignCenter)
        self.slice_input.setVisible(False)
        self.slice_input.returnPressed.connect(self._on_slice_input)
        self.slice_input.editingFinished.connect(self._on_slice_input_finished)

        nav_layout.addWidget(self.prev_button, alignment=Qt.AlignLeft)
        nav_layout.addWidget(self.slice_label, alignment=Qt.AlignCenter)
        nav_layout.addWidget(self.slice_input, alignment=Qt.AlignCenter)
        nav_layout.addWidget(self.next_button, alignment=Qt.AlignRight)

        layout.addLayout(nav_layout)

        self._zoom = 1.0
        self._original_pixmap = QPixmap()

        self.zoom_in_button.clicked.connect(
            lambda: self.set_zoom(self._zoom + 0.1)
        )
        self.zoom_out_button.clicked.connect(
            lambda: self.set_zoom(self._zoom - 0.1)
        )

        self.prev_button.clicked.connect(self._on_prev_slice)
        self.next_button.clicked.connect(self._on_next_slice)

    def set_pixmap(self, pixmap: QPixmap):
        """Set the pixmap of the image view widget."""
        self._original_pixmap = pixmap if pixmap is not None else QPixmap()
        self.set_zoom(1.0)

    def set_zoom(self, zoom: float):
        """Set the zoom of the image view widget."""
        zoom = max(0.5, min(zoom, 3.0))
        self._zoom = zoom

        if self._original_pixmap.isNull():
            self.image_label.clear()
            return

        # Scale to fit scroll area size
        available_size = self.scroll_area.viewport().size()
        scaled = self._original_pixmap.scaled(
            available_size * zoom,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)
        self.image_label.resize(scaled.size())

    def _on_slice_label_clicked(self, event):
        self.slice_label.setVisible(False)
        self.slice_input.setVisible(True)
        self.slice_input.setFocus()
        self.slice_input.selectAll()

    def _on_slice_input(self):
        self._editing = True
        try:
            index = int(self.slice_input.text())
            handler = self.controller.handler_registry.get_selected()
            if handler and handler["ui_properties"]["dim"] == 3:
                pass
        except ValueError:
            pass

        self._editing = False
        self.slice_input.setVisible(False)
        self.slice_label.setVisible(True)

    def _on_slice_input_finished(self):
        if self._editing:
            self._on_slice_input()

    def set_display_type(self, display_type: str):
        """Set the display type of the image view widget."""
        if display_type not in ["Raw Image", "Binarized Image"]:
            return
        self._current_display_type = display_type

        handler = self.controller.get_selected_handler()
        if handler is not None:
            handler["ui_properties"]["display_type"] = (
                self._current_display_type
            )

        self._update_image()

    def _update_image(self):
        handler = self.controller.get_selected_handler()
        if handler is None:
            self.set_pixmap(None)
            return
        index = handler["ui_properties"]["selected_slice_index"]
        image = None
        if self._current_display_type == "Raw Image":
            image = self.controller.get_selected_slice_raw_image(index)
        elif self._current_display_type == "Binarized Image":
            image = self.controller.get_selected_slice_binarized_image(index)

        if image is None:
            self.set_pixmap(None)
            return

        # Convert numpy array to QPixmap
        pixmap = self._numpy_to_pixmap(image)
        self.set_pixmap(pixmap)

        # Update slice label
        self._update_slice_label()

    def _numpy_to_pixmap(self, image: np.ndarray) -> QPixmap:
        """Convert numpy array to QPixmap."""
        if image is None:
            return QPixmap()

        image = np.ascontiguousarray(image)

        if len(image.shape) == 2:
            height, width = image.shape
            if image.dtype != np.uint8:
                image = (
                    (image - image.min())
                    / (image.max() - image.min() + 1e-10)
                    * 255
                )
                image = image.astype(np.uint8)
                image = np.ascontiguousarray(image)
            q_image = QImage(
                image.data, width, height, width, QImage.Format_Grayscale8
            )
        elif len(image.shape) == 3:
            height, width, channels = image.shape
            if channels == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                rgb_image = np.ascontiguousarray(rgb_image)
                q_image = QImage(
                    rgb_image.data,
                    width,
                    height,
                    width * 3,
                    QImage.Format_RGB888,
                )
            elif channels == 4:
                image = np.ascontiguousarray(image)
                q_image = QImage(
                    image.data,
                    width,
                    height,
                    width * 4,
                    QImage.Format_RGBA8888,
                )
            else:
                return QPixmap()
        else:
            return QPixmap()

        q_image = q_image.copy()
        return QPixmap.fromImage(q_image)

    def _update_slice_label(self):
        """Update the slice label with current slice information."""
        if self.controller is None:
            self.slice_label.setText("0 / 0")
            return

        handler = self.controller.handler_registry.get_selected()
        if handler is None:
            self.slice_label.setText("0 / 0")
            return

        slice_index = handler["ui_properties"].get("selected_slice_index", 0)
        dim = handler["ui_properties"].get("dim", 2)

        if dim == 2:
            # 2D image, only one slice
            self.slice_label.setText("1 / 1")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
        elif dim == 3:
            # 3D image, multiple slices
            image_shape = handler["ui_properties"].get("image_shape", None)
            if image_shape is not None and len(image_shape) >= 3:
                total_slices = image_shape[0]
                current_slice = slice_index + 1  # Display 1-indexed
                self.slice_label.setText(f"{current_slice} / {total_slices}")
                self.prev_button.setEnabled(slice_index > 0)
                self.next_button.setEnabled(slice_index < total_slices - 1)
            else:
                self.slice_label.setText(f"{slice_index + 1} / ?")
        else:
            self.slice_label.setText("0 / 0")

    def _on_prev_slice(self):
        handler = self.controller.get_selected_handler()
        if handler is None:
            return

        index = handler["ui_properties"]["selected_slice_index"]
        if index > 0:
            self.controller.set_selected_slice_index(index - 1)
            self._update_image()

    def _on_next_slice(self):
        handler = self.controller.get_selected_handler()
        if handler is None:
            return

        index = handler["ui_properties"]["selected_slice_index"]
        total_slices = handler["ui_properties"]["image_shape"][0]
        if index < total_slices - 1:
            self.controller.set_selected_slice_index(index + 1)
            self._update_image()

    def refresh(self):
        """Refresh the image view widget."""
        handler = self.controller.get_selected_handler()
        if handler is None:
            self.image_label.clear()
            self._original_pixmap = QPixmap()
            self.slice_label.setText("0 / 0")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            return
        self._current_display_type = handler["ui_properties"]["display_type"]
        self._update_image()

    def refresh_ui(self, theme: str):
        """Refresh the icons of the image view widget."""
        self.zoom_in_button.setIcon(QIcon(get_icon_path("zoom_in.png", theme)))
        self.zoom_out_button.setIcon(
            QIcon(get_icon_path("zoom_out.png", theme))
        )
        self.prev_button.setIcon(QIcon(get_icon_path("previous.png", theme)))
        self.next_button.setIcon(QIcon(get_icon_path("next.png", theme)))
