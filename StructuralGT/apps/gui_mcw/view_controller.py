import logging
import pathlib
import sys
from typing import Optional

import cv2
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from ovito import scene
from ovito.gui import create_qwidget
from ovito.io import import_file
from ovito.vis import Viewport
from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtWidgets import QApplication

from .handler import HandlerRegistry, NetworkHandler, PointNetworkHandler


class ImageViewController:
    """Class to manage image visualization in the GUI."""

    def __init__(self, registry: HandlerRegistry):
        self.registry = registry

    @staticmethod
    def get_pixmap(selected_index: int) -> str:
        """Return the URL that QML should use to load the image."""
        rng = np.random.default_rng()
        curr_img_view = rng.integers(0, 4)
        unique_num = (
            selected_index
            + curr_img_view
            + rng.integers(low=21, high=1000)
        )
        return f"image://imageProvider/{unique_num}"

    def get_display_info(self) -> dict:
        """Return display type, selected slice index, and number of slices."""
        handler = self.registry.get_selected()

        if not handler or not isinstance(handler, NetworkHandler):
            return {
                "pixmap": "",
                "display_type": "",
                "selected_slice": -1,
                "number_of_slices": 0
            }

        display_type = handler.display_type
        selected_slice = handler.selected_slice_index if handler.dim == 3 else 0
        num_slices = handler.network.image.shape[0] if handler.dim == 3 else 1

        return {
            "pixmap": self.get_pixmap(selected_slice),
            "display_type": display_type,
            "selected_slice": selected_slice,
            "number_of_slices": num_slices
        }

    def set_selected_slice_index(self, index: int) -> bool:
        """Set the selected slice index of the selected image."""
        handler = self.registry.get_selected()
        if (
            handler
            and isinstance(handler, NetworkHandler)
            and 0 <= index < handler.network.image.shape[0]
        ):
            handler.selected_slice_index = index
            return True
        return False

    def get_raw_image(self) -> np.ndarray | None:
        """Get the raw image of the selected network."""
        handler = self.registry.get_selected()
        image = None

        if handler and isinstance(handler, NetworkHandler):
            image = handler.network.image
            if handler.dim == 3:
                image = image[handler.selected_slice_index, :, :]

        return image

    def get_binarized_image(self) -> np.ndarray | None:
        """Get the binarized image of the selected NetworkHandler."""
        handler = self.registry.get_selected()
        image = None

        if handler and isinstance(handler, NetworkHandler):
            binarized_dir = (
                "/Binarized/slice" +
                str(handler.selected_slice_index+1).zfill(4) +
                ".tiff" if handler.dim == 3 else "/Binarized/slice0000.tiff"
            )
            image = cv2.imread(handler.input_dir + binarized_dir)

        return image

    def get_extracted_graph_image(self) -> np.ndarray | None:
        """Get the image of extracted graph of the selected NetworkHandler."""
        handler = self.registry.get_selected()
        image = None

        if handler and isinstance(handler, NetworkHandler) and handler.dim == 2:
            ax = handler.network.graph_plot()
            fig = ax.get_figure()
            fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

            canvas = FigureCanvasAgg(fig)
            canvas.draw()

            width, height = canvas.get_width_height()

            buf = canvas.buffer_rgba()
            image = np.asarray(buf, dtype=np.uint8).reshape((height, width, 4))

        return image

class GraphViewController:
    """Class to manage graph visualization in the GUI."""

    def __init__(
            self,
            registry: HandlerRegistry,
            qml_app: QApplication,
            qml_engine: QQmlApplicationEngine):
        self.registry = registry
        self.qml_app = qml_app
        self.qml_engine = qml_engine
        self.container_object_name = "graphPage"
        self.viewport = Viewport(
            type=Viewport.Type.Perspective, camera_dir=(2, 1, -1)
        )
        container = self._find_container()
        if not container:
            logging.error(f"Graph container '{self.container_object_name}' not found.")
            return
        self.ovito_widget = create_qwidget(
            self.viewport, parent=container
        )

    def render_graph(self) -> bool:
        """Construct scene and mount it to the qml engine."""
        gsd_file = self._find_gsd_file()
        if not gsd_file:
            logging.error("No GSD file found for the selected handler.")
            return False
        if not pathlib.Path(gsd_file).exists():
            logging.error(f"GSD file '{gsd_file}' does not exist.")
            return False

        try:
            for p in list(scene.pipelines):
                p.remove_from_scene()

            pipeline = import_file(gsd_file)
            pipeline.add_to_scene()

        except Exception as e:
            logging.error(f"Error rendering graph: {e}")
            return False

        return True

    def _find_container(self) -> Optional[QQuickItem]:
        """Find the container object in the QML engine."""
        roots = self.qml_engine.rootObjects()
        if not roots:
            return None
        root = roots[0]
        return root.findChild(QQuickItem, self.container_object_name)

    def _find_gsd_file(self) -> Optional[str]:
        """Find the GSD file associated with the selected NetworkHandler."""
        handler = self.registry.get_selected()

        gsd_file = None
        if handler and isinstance(handler, NetworkHandler):
            gsd_file = handler.input_dir + "Binarized/network.gsd"
        elif handler and isinstance(handler, PointNetworkHandler):
            gsd_file = handler.input_dir + "skel.gsd"

        return gsd_file
