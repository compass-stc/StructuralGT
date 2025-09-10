import json
import logging
import uuid

from PySide6.QtCore import QObject, Slot
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from StructuralGT import __version__

from ..model.list_model import ListModel
from ..model.table_model import TableModel
from ..utils.handler import HandlerRegistry, PointNetworkHandler
from ..utils.task import (
    BinarizeTask,
    ExtractGraphTask,
    GraphAnalysisTask,
)
from .file_controller import FileController
from .signal_controller import SIGNAL_CONTROLLER
from .task_controller import TaskController
from .view_controller import GraphViewController, ImageViewController


class MainController(QObject):
    """Exposes a method to refresh the image in QML."""

    def __init__(self, qml_app: QApplication, qml_engine: QQmlApplicationEngine):
        super().__init__()
        self.qml_app = qml_app
        self.qml_engine = qml_engine

        self.registry = HandlerRegistry()
        self.file_ctrl = FileController(self.registry)
        self.image_view_ctrl = ImageViewController(self.registry)
        self.graph_view_ctrl = GraphViewController(
            self.registry, self.qml_app, self.qml_engine
        )
        self.task_ctrl = TaskController(self.registry)

        # Create Models
        self.imagePropsModel = TableModel([])
        self.graphPropsModel = TableModel([])
        self.networkListModel = ListModel([])

        # Expose SignalController signals directly for QML access
        self.imageRefreshSignal = SIGNAL_CONTROLLER.imageRefreshSignal
        self.imageRefreshedSignal = SIGNAL_CONTROLLER.imageRefreshedSignal
        self.imageChangedSignal = SIGNAL_CONTROLLER.imageChangedSignal
        self.graphRefreshSignal = SIGNAL_CONTROLLER.graphRefreshSignal
        self.alertShowSignal = SIGNAL_CONTROLLER.alertShowSignal

        # Connect signals
        self._connect_signals()

    def _connect_signals(self):
        """Connect signals to handlers."""
        # Connect image refresh signal to update image model
        SIGNAL_CONTROLLER.connect_signal("imageRefreshSignal", self.update_image_model)

        # Connect graph refresh signal to update graph model
        SIGNAL_CONTROLLER.connect_signal("graphRefreshSignal", self.update_graph_model)

        # Connect task completion signals
        SIGNAL_CONTROLLER.connect_signal(
            "taskFinishedWithInfo", self._on_task_finished_with_info
        )

    def cleanup(self):
        """Clean up resources when application is closing."""
        logging.info("Cleaning up MainController...")

        # Clean up task controller
        if hasattr(self, "task_ctrl"):
            self.task_ctrl.cleanup()

        # Disconnect signals
        SIGNAL_CONTROLLER.disconnect_signal(
            "imageRefreshSignal", self.update_image_model
        )
        SIGNAL_CONTROLLER.disconnect_signal(
            "graphRefreshSignal", self.update_graph_model
        )
        SIGNAL_CONTROLLER.disconnect_signal(
            "taskFinishedWithInfo", self._on_task_finished_with_info
        )

        logging.info("MainController cleanup completed")

    @Slot(result=bool)
    def img_loaded(self):
        """Check if an image is loaded."""
        handler = self.registry.get_selected()
        return (
            handler is not None
            and hasattr(handler, "img_loaded")
            and handler.img_loaded
        )

    @Slot(str, int)
    def add_network(self, path: str, dim: int):
        """Add a network for the given path and dimension."""
        handler = self.file_ctrl.create_network_handler(path, dim)
        if handler is None:
            SIGNAL_CONTROLLER.emit_signal(
                "alertShowSignal", "Network Error", "Error creating network."
            )
        else:
            self.registry.add(handler)
            self.registry.select(self.registry.count() - 1)
            self.networkListModel.reset_data(self.registry.list_for_ui())
            SIGNAL_CONTROLLER.emit_signal("imageRefreshSignal")
            SIGNAL_CONTROLLER.emit_signal("graphRefreshSignal")

    @Slot(str, float)
    def add_point_network(self, path: str, cutoff: float):
        """Add a point network for the given path and dimension."""
        handler = self.file_ctrl.create_point_network_handler(path, cutoff)
        if handler is None:
            SIGNAL_CONTROLLER.emit_signal(
                "alertShowSignal",
                "Point Network Error",
                "Error creating point network.",
            )
        else:
            self.registry.add(handler)
            self.registry.select(self.registry.count() - 1)
            self.networkListModel.reset_data(self.registry.list_for_ui())
            SIGNAL_CONTROLLER.emit_signal("graphRefreshSignal")

    @Slot(int)
    def delete_network(self, index: int):
        """Delete a network from the registry."""
        # Validate index
        if index < 0 or index >= self.registry.count():
            SIGNAL_CONTROLLER.emit_signal(
                "alertShowSignal", "Delete Error", f"Invalid network index: {index}"
            )
            return

        # Get network info for logging
        handler = self.registry.get(index)
        network_name = handler.input_dir if handler else f"index {index}"

        # Delete the network
        if not self.registry.delete(index):
            SIGNAL_CONTROLLER.emit_signal(
                "alertShowSignal",
                "Delete Error",
                f"Failed to delete network at index {index}",
            )
            return

        # Update the network list model
        self.networkListModel.reset_data(self.registry.list_for_ui())

        # Clear models if no networks left
        if self.registry.count() == 0:
            self.imagePropsModel.reset_data([])
            self.graphPropsModel.reset_data([])
            logging.info("All networks deleted, cleared property models")
        else:
            # Refresh current view if we still have networks
            self.refresh_image_view()
            self.update_graph_model()

        logging.info(f"Deleted network: {network_name}")

        # Show success message
        SIGNAL_CONTROLLER.emit_signal(
            "alertShowSignal",
            "Delete Success",
            f"Successfully deleted network: {network_name}",
        )

    @Slot()
    def delete_all_networks(self):
        """Delete all networks from the registry."""
        if self.registry.count() == 0:
            SIGNAL_CONTROLLER.emit_signal(
                "alertShowSignal", "Delete Info", "No networks to delete"
            )
            return

        # Delete all networks
        self.registry.delete_all()

        # Clear all models
        self.networkListModel.reset_data([])
        self.imagePropsModel.reset_data([])
        self.graphPropsModel.reset_data([])

        logging.info("All networks deleted")

        # Show success message
        SIGNAL_CONTROLLER.emit_signal(
            "alertShowSignal", "Delete Success", "Successfully deleted all networks"
        )

    @Slot()
    def refresh_image_view(self):
        """Refresh the image in the GUI."""
        try:
            SIGNAL_CONTROLLER.emit_signal("imageRefreshSignal")
        except Exception as e:
            logging.exception("Image Loading Error: %s", e, extra={"user": "SGT Logs"})
            SIGNAL_CONTROLLER.emit_signal(
                "alertShowSignal", "Image Error", "Error loading image. Try again."
            )

    @Slot(result=str)
    def get_display_info(self):
        """Get display information for the current image."""
        info = self.image_view_ctrl.get_display_info()
        return json.dumps(info)

    @Slot(str)
    def set_display_type(self, display_type: str):
        """Set the display type for the image view."""
        self.image_view_ctrl.set_display_type(display_type)
        self.refresh_image_view()

    @Slot(int)
    def set_selected_slice_index(self, index):
        """Set the selected slice index of the selected image."""
        self.image_view_ctrl.set_selected_slice_index(index)
        self.refresh_image_view()

    @Slot(int)
    def set_selected_index(self, index):
        """Set the selected index of the image list."""
        self.registry.select(index)
        self.refresh_image_view()

    @Slot(QObject)
    def refresh_graph_view(self, container: QObject):
        """Refresh the graph in the GUI."""
        try:
            if not self.graph_view_ctrl.ovito_widget:
                self.graph_view_ctrl.attach_after_qml_loaded(container)
            if self.registry.get_selected() is None:
                return
            self.graph_view_ctrl.render_graph()
            self.update_graph_model()
        except Exception as e:
            logging.exception("Graph Refresh Error: %s", e, extra={"user": "SGT Logs"})
            SIGNAL_CONTROLLER.emit_signal(
                "alertShowSignal", "Graph Error", "Error refreshing graph. Try again."
            )

    @Slot(str)
    def submit_binarize_task(self, options: str):
        """Submit a binarization task."""
        # Assign unique ID
        id = str(uuid.uuid4())
        task = BinarizeTask(
            id=id, index=self.registry.get_selected_index(), options=json.loads(options)
        )
        self.task_ctrl.enqueue(task)

    @Slot(str)
    def submit_extract_graph_task(self, weights: str):
        """Submit a graph extraction task."""
        # Assign unique ID
        id = str(uuid.uuid4())
        task = ExtractGraphTask(
            id=id, index=self.registry.get_selected_index(), weights=weights
        )
        self.task_ctrl.enqueue(task)

    @Slot(str)
    def submit_graph_analysis_task(self, options: str):
        """Submit a graph analysis task."""
        # Assign unique ID
        id = str(uuid.uuid4())
        task = GraphAnalysisTask(
            id=id, index=self.registry.get_selected_index(), options=json.loads(options)
        )
        self.task_ctrl.enqueue(task)

    @Slot()
    def update_image_model(self):
        """Update the image properties model with the selected image's properties."""
        handler = self.registry.get_selected()

        if handler is None or isinstance(handler, PointNetworkHandler):
            self.imagePropsModel.reset_data([])
            return

        if handler.dim == 3:
            image_props = [
                ["Name", f"{handler.input_dir}"],
                [
                    "Depth x Height x Width",
                    f"{handler.network.image.shape[0]} x {handler.network.image.shape[1]} x {handler.network.image.shape[2]}",
                ],
                ["Dimensions", "3D"],
            ]
        else:
            image_props = [
                ["Name", f"{handler.input_dir}"],
                [
                    "Height x Width",
                    f"{handler.network.image.shape[0]} x {handler.network.image.shape[1]}",
                ],
                ["Dimensions", "2D"],
            ]

        self.imagePropsModel.reset_data(image_props)
        logging.info(f"Updated image properties model: {image_props}")

    @Slot()
    def update_graph_model(self):
        """Update the graph properties model."""
        handler = self.registry.get_selected()

        if handler is None:
            return

        # Check if graph is available (either loaded or for PointNetworkHandler)
        if isinstance(handler, PointNetworkHandler) or (
            hasattr(handler, "graph_loaded") and handler.graph_loaded
        ):
            graph_props = [
                ["Edge Count", f"{handler.network.graph.ecount()}"],
                ["Node Count", f"{handler.network.graph.vcount()}"],
            ]

            # Add analysis properties if they exist
            for key, value in handler.properties.items():
                if value is not None and value != "":
                    graph_props.append([key, f"{value:.5f}"])

            self.graphPropsModel.reset_data(graph_props)
            logging.info(f"Updated graph properties model: {graph_props}")
        else:
            # No graph available, clear the model
            self.graphPropsModel.reset_data([])
            logging.info("No graph available, cleared graph properties model")

    @Slot(object, bool)
    def _on_task_finished_with_info(self, task, success: bool):
        """Handle task completion with automatic UI updates."""
        logging.info(f"Task finished: {task.type}, success: {success}")

        if not success:
            logging.warning(f"Task {task.type} failed, skipping UI updates")
            return

        task_type = task.type

        if task_type == "binarize":
            # Apply filter and switch to binarized view
            self.image_view_ctrl.set_display_type("binarized")
            SIGNAL_CONTROLLER.emit_signal("imageRefreshSignal")
            logging.info("Binarize task completed, switched to binarized view")

        elif task_type == "extract_graph":
            # Extracted graph and switch to extracted graph view (for 2D case only)
            handler = self.registry.get_selected()
            if handler and hasattr(handler, "dim") and handler.dim == 2:
                self.image_view_ctrl.set_display_type("extracted")
                SIGNAL_CONTROLLER.emit_signal("imageRefreshSignal")
                logging.info("Extract graph task completed, switched to extracted view")

        elif task_type == "graph_analysis":
            # Update graph properties model
            logging.info("Graph analysis task completed, updating graph properties...")
            self.update_graph_model()
            # Trigger image refresh signal to update QML visibility
            SIGNAL_CONTROLLER.emit_signal("imageRefreshedSignal")
            logging.info("Graph properties updated successfully")

    @Slot(str, result=str)
    def get_file_extensions(self, option):
        """Return the file extensions for the specified option."""
        return self.file_ctrl.file_filters(option)

    @Slot(result=str)
    def get_sgt_version(self):
        """Return the version of StructuralGT."""
        # Copyright (C) 2024, the Regents of the University of Michigan.
        return f"StructuralGT v{__version__}"

    @Slot(result=str)
    def get_about_details(self):
        """Return the about details of the application."""
        return (
            f"A software tool that allows graph theory analysis of nano-structures. This is a modified version "  # noqa: E501
            "of StructuralGT initially proposed by Drew A. Vecchio, DOI: "
            "<html><a href='https://pubs.acs.org/doi/10.1021/acsnano.1c04711'>10.1021/acsnano.1c04711</a></html><html><br/><br/></html>"
            "Contributors:<html><br/></html>"
            "1. Nicolas Kotov<html><br/></html>"
            "2. Dickson Owuor<html><br/></html>"
            "3. Alain Kadar<html><br/><br/></html>"
            "Documentation:<html><br/></html>"
            "<html><a href='https://structuralgt.readthedocs.io'>structuralgt.readthedocs.io</a></html><html><br/><br/></html>"
            f"{self.get_sgt_version()}<html><br/></html>"
            "Copyright (C) 2018-2025, The Regents of the University of Michigan.<html><br/></html>"  # noqa: E501
            "License: GPL GNU v3<html><br/></html>"
        )
