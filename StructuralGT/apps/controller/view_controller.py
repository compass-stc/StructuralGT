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
from PySide6.QtCore import QPoint, QPointF, QRect, QSize, Qt, QTimer
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtWidgets import QApplication

from ..utils.handler import HandlerRegistry, NetworkHandler, PointNetworkHandler


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

    def set_display_type(self, display_type: str) -> bool:
        """Set the display type for the image view."""
        handler = self.registry.get_selected()
        if handler and isinstance(handler, NetworkHandler):
            handler.display_type = display_type
            return True
        return False

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
            try:
                image = handler.network.image
                if handler.dim == 3:
                    image = image[handler.selected_slice_index, :, :]
            except Exception as e:
                logging.exception("Error loading raw image: %s", e)
        return image

    def get_binarized_image(self) -> np.ndarray | None:
        """Get the binarized image of the selected NetworkHandler."""
        handler = self.registry.get_selected()
        image = None

        if handler and isinstance(handler, NetworkHandler):
            if handler.binary_loaded is False:
                return None

            try:
                binarized_dir = (
                    "/Binarized/slice" +
                    str(handler.selected_slice_index+1).zfill(4) +
                    ".tiff" if handler.dim == 3 else "/Binarized/slice0000.tiff"
                )
                image = cv2.imread(handler.input_dir + binarized_dir)
                logging.info(handler.options)
            except Exception as e:
                logging.exception("Error loading binarized image: %s", e)
        return image

    def get_extracted_graph_image(self) -> np.ndarray | None:
        """Get the image of extracted graph of the selected NetworkHandler."""
        handler = self.registry.get_selected()
        image = None

        if handler and isinstance(handler, NetworkHandler) and handler.dim == 2:
            if handler.graph_loaded is False:
                return None

            try:
                ax = handler.network.graph_plot()
                fig = ax.get_figure()
                fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

                canvas = FigureCanvasAgg(fig)
                canvas.draw()

                width, height = canvas.get_width_height()

                buf = canvas.buffer_rgba()
                image = np.asarray(buf, dtype=np.uint8).reshape((height, width, 4))
            except Exception as e:
                logging.exception("Error loading extracted graph image: %s", e)
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
        self.viewport = Viewport(
            type=Viewport.Type.Perspective, camera_dir=(2, 1, -1)
        )
        self.ovito_widget = None
        self._container: QQuickItem | None = None
        self._window: QQuickWindow | None = None
        self._coalesce_timer = QTimer()
        self._coalesce_timer.setSingleShot(True)
        self._coalesce_timer.setInterval(0)
        self._coalesce_timer.timeout.connect(lambda: self._sync_to_container())

    def attach_after_qml_loaded(self, container: QQuickItem) -> bool:
        """Attach the Ovito widget to QML container after loaded."""
        if not container:
            logging.error("Graph container not found.")
            return False
        logging.info(
            f"Attaching Ovito widget to QML container {container.objectName()}"
        )
        self._container = container
        self._window = container.window()
        self.ovito_widget = create_qwidget(self.viewport, parent=None)
        self.ovito_widget.setWindowFlag(Qt.Tool, True)
        self.ovito_widget.setWindowFlag(Qt.FramelessWindowHint, True)
        if self.ovito_widget.windowHandle() is not None:
            self.ovito_widget.windowHandle().setParent(self._window)
        self._hook_geometry_signals()
        self._sync_to_container()
        self.ovito_widget.show()
        logging.info(
            f"Ovito widget attached to QML container {container.objectName()}."
        )
        return True

    def _queue_sync(self):
        self._sync_to_container()
        if self._coalesce_timer.isActive():
            self._coalesce_timer.start()
        self._coalesce_timer.start(0)

    def _hook_geometry_signals(self):
        c = self._container
        w = self._window
        if not c or not w:
            return

        for sig in (
            c.widthChanged, c.heightChanged, c.xChanged, c.yChanged, c.visibleChanged
        ):
            sig.connect(lambda *_, f=self._queue_sync: f())

        for sig in (
            w.xChanged, w.yChanged, w.widthChanged,
            w.heightChanged, w.visibilityChanged, w.windowStateChanged
        ):
            sig.connect(lambda *_, f=self._queue_sync: f())

    def _sync_to_container(self):
        o = self.ovito_widget
        c = self._container
        w = self._window
        if not o or not c or not w:
            return

        minimized = bool(w.windowState() & Qt.WindowMinimized)
        hidden = (w.visibility() == QQuickWindow.Hidden)
        visible = c.isVisible() and w.isVisible() and not minimized and not hidden

        if visible:
            if not o.isVisible():
                o.show()
        else:
            if o.isVisible():
                o.hide()

        scene_pos: QPointF = c.mapToScene(QPointF(0, 0))
        global_pos: QPoint = w.mapToGlobal(
            QPoint(int(scene_pos.x()), int(scene_pos.y())))
        width = int(c.width())
        height = int(c.height())
        o.setGeometry(QRect(global_pos, QSize(width, height)))
        o.raise_()
        self.viewport.zoom_all()
        logging.debug(f"Ovito widget geometry updated: {global_pos}, {width}x{height}")

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

    def _find_gsd_file(self) -> Optional[str]:
        """Find the GSD file associated with the selected NetworkHandler."""
        handler = self.registry.get_selected()

        gsd_file = None
        if handler and isinstance(handler, NetworkHandler):
            gsd_file = handler.input_dir + "Binarized/network.gsd"
        elif handler and isinstance(handler, PointNetworkHandler):
            gsd_file = pathlib.Path(handler.input_dir).parent / "skel.gsd"

        return gsd_file
