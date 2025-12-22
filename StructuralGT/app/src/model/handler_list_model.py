"""List model for the StructuralGT GUI."""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from typing import Any, Optional
from model.handler import (
    HandlerRegistry,
    Handler,
    NetworkHandler,
    PointNetworkHandler,
)
from StructuralGT.networks import Network, PointNetwork


class HandlerListModel(QAbstractListModel):
    """List model for displaying Network/PointNetwork Handlers."""

    data_changed_signal = Signal(QModelIndex, QModelIndex)

    def __init__(self, handler_registry: HandlerRegistry):
        """Initialize the handler list model."""
        super().__init__()
        self.handler_registry = handler_registry
        self._thumbnail_cache = {}
        self._thumbnail_size = 64

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows in the list."""
        if parent.isValid():
            return 0
        return self.handler_registry.count()

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """Return the data for the given index and role."""
        if not index.isValid():
            return None

        handler, handler_index = self._get_handler_at_index(index.row())
        if handler is None or handler_index is None:
            return None

        if role == Qt.DisplayRole:
            return self._get_display_name(handler)
        elif role == Qt.DecorationRole:
            return self._get_thumbnail(handler, handler_index)
        elif role == Qt.UserRole:
            return handler_index
        elif role == Qt.UserRole + 1:
            return self._get_handler_type(handler)
        elif role == Qt.UserRole + 2:
            return self._get_image_binarized(handler)
        elif role == Qt.UserRole + 3:
            return self._get_graph_extracted(handler)

        return None

    def refresh(self):
        """Refresh the list model."""
        self._thumbnail_cache.clear()
        self.beginResetModel()
        self.endResetModel()

    def _get_handler_at_index(
        self, row: int
    ) -> tuple[Optional[Handler], Optional[int]]:
        """Map list index to HandlerRegistry index."""
        valid_indices = self._get_valid_indices()
        if row < len(valid_indices):
            handler_index = valid_indices[row]
            handler = self.handler_registry.get(handler_index)
            return handler, handler_index
        return None, None

    def _get_valid_indices(self) -> list[int]:
        """Get the valid indices list from HandlerRegistry."""
        return self.handler_registry.get_valid_indices()

    def _get_display_name(self, handler: Handler) -> str:
        """Get the display name for the given handler."""
        input_dir = handler["paths"]["input_dir"]
        if input_dir:
            return Path(input_dir).name
        return "Unknown"

    def _get_thumbnail(
        self, handler: Handler, index: int
    ) -> Optional[QPixmap]:
        """Get the thumbnail for the given handler."""
        if index in self._thumbnail_cache:
            return self._thumbnail_cache[index]

        network = handler["network"]
        if isinstance(network, Network):
            image_array = network.image
            thumbnail = self._generate_thumbnail(image_array)
        elif isinstance(network, PointNetwork):
            thumbnail = (
                None  # TODO: Determine the thumbnail for point networks
            )
        else:
            return None

        if thumbnail:
            self._thumbnail_cache[index] = thumbnail
            return thumbnail
        return None

    def _generate_thumbnail(
        self, image_array: np.ndarray
    ) -> Optional[QPixmap]:
        """Generate the thumbnail for 2D and 3D images."""
        if image_array is None or image_array.size == 0:
            return None

        dim = len(image_array.shape)
        if dim != 2 and dim != 3:
            return None

        image = image_array[0, :, :] if dim == 3 else image_array
        image = cv2.normalize(
            image, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U
        )
        thumbnail = cv2.resize(
            image,
            (self._thumbnail_size, self._thumbnail_size),
            interpolation=cv2.INTER_AREA,
        )

        h, w = thumbnail.shape
        q_image = QImage(thumbnail.data, w, h, w, QImage.Format_Grayscale8)
        return QPixmap.fromImage(q_image)

    def _get_handler_type(self, handler: Handler) -> str:
        """Get the handler type for the given handler."""
        ui_props = handler["ui_properties"]
        dim = ui_props.get("dim")
        if dim is None:
            return "Unknown"

        if isinstance(handler, NetworkHandler):
            return f"{dim}D Network"
        elif isinstance(handler, PointNetworkHandler):
            return "Point Network"
        return "Unknown"

    def _get_image_binarized(self, handler: Handler) -> bool:
        """Get the binarized image loaded status for the given handler."""
        ui_props = handler["ui_properties"]
        return ui_props.get("binarized_loaded", False)

    def _get_graph_extracted(self, handler: Handler) -> bool:
        """Get the graph extracted status for the given handler."""
        ui_props = handler["ui_properties"]
        return ui_props.get("extracted_loaded", False)
