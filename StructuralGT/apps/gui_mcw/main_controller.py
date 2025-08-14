import json
import logging
import os
import shutil
import sys
import tempfile
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from ovito import scene
from ovito.gui import create_qwidget
from ovito.io import import_file
from ovito.vis import Viewport
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from StructuralGT import __version__
from StructuralGT.networks import PointNetwork

from .csv_handler import CSVHandler
from .file_controller import FileController
from .handler import HandlerRegistry, NetworkHandler, PointNetworkHandler
from .list_model import ListModel
from .qthread_worker import QThreadWorker, WorkerTask
from .table_model import TableModel
from .view_controller import GraphViewController, ImageViewController


class MainController(QObject):
    """Exposes a method to refresh the image in QML."""

    # Signals
    refreshImageSignal = Signal()  # noqa: N815
    imageRefreshedSignal = Signal()  # noqa: N815
    showAlertSignal = Signal(str, str)  # noqa: N815


    errorSignal = Signal(str)
    changeImageSignal = Signal()
    imageChangedSignal = Signal()
    taskFinishedSignal = Signal(
        bool, object
    )  # success/fail (True/False), result (object)

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

        # Create QThreadWorker for long tasks
        self.wait_flag = False
        self.worker_task = WorkerTask()
        self.thread = QThreadWorker(None, None)

        # Create Models
        self.imagePropsModel = TableModel([])
        self.graphPropsModel = TableModel([])
        self.imageListModel = ListModel([])

    @Slot(str, int)
    def add_network(self, path: str, dim: int):
        """Add a network for the given path and dimension."""
        handler = self.file_ctrl.create_network_handler(path, dim)
        if handler is None:
            self.showAlertSignal.emit("Network Error", "Error creating network.")
        else:
            self.registry.add(handler)
            self.registry.select(self.registry.count() - 1)
            self.refresh_image_view()

    @Slot(str, float)
    def add_point_network(self, path: str, cutoff: float):
        """Add a point network for the given path and dimension."""
        handler = self.file_ctrl.create_point_network_handler(path, cutoff)
        if handler is None:
            self.showAlertSignal.emit(
                "Point Network Error", "Error creating point network."
            )
        else:
            self.registry.add(handler)
            self.registry.select(self.registry.count() - 1)
            self.refresh_image_view()

    @Slot()
    def refresh_image_view(self):
        """Refresh the image in the GUI."""
        try:
            self.refreshImageSignal.emit()
        except Exception as e:
            logging.exception(
                "Image Loading Error: %s", e, extra={"user": "SGT Logs"}
            )
            self.showAlertSignal.emit(
                "Image Error", "Error loading image. Try again."
            )

    @Slot(result=str)
    def get_display_info(self):
        """Get display information for the current image."""
        info = self.image_view_ctrl.get_display_info()
        return json.dumps(info)

    @Slot(int)
    def set_selected_slice_index(self, index):
        """Set the selected slice index of the selected image."""
        self.image_view_ctrl.set_selected_slice_index(index)
        self.refresh_image_view()

    @Slot(str)
    def run_binarizer(self, options):
        """Run the binarizer on the selected image"""
        if self.wait_flag:
            logging.info(
                "Please Wait: Another Task Running!",
                extra={"user": "SGT Logs"},
            )
            self.showAlertSignal.emit("Please Wait", "Another Task Running!")
            return

        handler = self.file_controller.get_selected_handler()
        if handler is None:
            self.wait_flag = False
            return

        self.wait_flag = True
        if options:
            handler.options = json.loads(options)

        self.thread = QThreadWorker(
            self.worker_task.task_run_binarizer,
            (handler,),
        )

        self.worker_task.taskFinishedSignal.connect(
            self._on_binarizer_finished
        )
        self.worker_task.taskFinishedSignal.connect(self.thread.quit)

        self.thread.start()

    @Slot(bool, object)
    def _on_binarizer_finished(self, success, result):
        self.wait_flag = False
        if success:
            self.toggle_current_img_view("binary")
        else:
            self.showAlertSignal.emit(
                "Binarizer Error", "Error applying binarizer."
            )

    @Slot()
    def run_graph_extraction(self):
        """Run the graph extraction on the selected image"""
        self.run_graph_extraction_with_weights("")
    
    @Slot(str)
    def run_graph_extraction_with_weights(self, weights):
        """Run the graph extraction on the selected image with weights"""
        if self.wait_flag:
            logging.info(
                "Please Wait: Another Task Running!",
                extra={"user": "SGT Logs"},
            )
            self.showAlertSignal.emit("Please Wait", "Another Task Running!")
            return

        handler = self.file_controller.get_selected_handler()
        if handler is None:
            self.wait_flag = False
            return

        # Ensure binary image is available before graph extraction
        if not handler.binary_loaded:
            self.showAlertSignal.emit(
                "Binary Image Required", 
                "Please apply binarizer before extracting graph."
            )
            return

        self.wait_flag = True
        self.thread = QThreadWorker(
            self.worker_task.task_run_graph_extraction,
            (handler, weights),
        )
        self.worker_task.taskFinishedSignal.connect(
            self._on_graph_extraction_finished
        )
        self.worker_task.taskFinishedSignal.connect(self.thread.quit)
        self.thread.start()

    @Slot(bool, object)
    def _on_graph_extraction_finished(self, success, result):
        self.wait_flag = False
        if success:
            self.toggle_current_img_view("graph")
        else:
            self.showAlertSignal.emit(result[0], result[1])

    # TODO: account for point network
    @Slot(str, result=bool)
    def toggle_current_img_view(self, display_type):
        print(f"Display type: {display_type}")

        image = self.file_controller.get_selected_handler()

        if display_type == "binary" and not image.binary_loaded:
            # Use the default options
            self.run_binarizer(options=None)
            return False
        elif display_type == "graph" and not image.graph_loaded:
            self.run_graph_extraction()
            return False
        elif image.display_type == display_type:
            return True
        else:
            image.display_type = display_type
            self.load_image()
            return True

    # TODO: make it compatible with point network
    def load_graph(self):
        """Render and visualize OVITO graph network simulation."""
        try:

            # Clear any existing scene
            for p_line in list(scene.pipelines):
                p_line.remove_from_scene()

            # Find the QML Rectangle to embed into
            root = self.qml_engine.rootObjects()[0]
            graph_container = root.findChild(QObject, "graphContainer")

            if graph_container:

                # Grab rectangle properties
                x = graph_container.property("x")
                y = graph_container.property("y")
                w = graph_container.property("width")
                h = graph_container.property("height")

                # Create OVITO data pipeline
                handler = self.file_controller.get_selected_handler()
                if isinstance(handler, PointNetworkHandler):
                    gsd_file = os.path.join(os.path.dirname(handler.path), "skel.gsd")
                elif isinstance(handler, NetworkHandler):
                    gsd_file = os.path.join(handler.path, "Binarized/network.gsd")
                pipeline = import_file(gsd_file)
                pipeline.add_to_scene()

                vp = Viewport(type=Viewport.Type.Perspective, camera_dir=(2, 1, -1))
                ovito_widget = create_qwidget(vp, parent=self.qml_app.activeWindow())
                ovito_widget.setMinimumSize(800, 500)
                vp.zoom_all((800, 500))

                # Re-parent OVITO QWidget
                ovito_widget.setGeometry(x, y, w, h)
                ovito_widget.show()

        except Exception as e:
            print("Graph Simulation Error:", e)


    @Slot()
    def update_image_model(self):
        """Update the image properties model with the selected image's properties."""
        handler = self.file_controller.get_selected_handler()

        if handler is None or isinstance(handler, PointNetworkHandler):
            self.imagePropsModel.reset_data([])
            return

        if handler.dim == 3:
            image_props = [
                ["Name", f"{handler.path}"],
                ["Depth x Height x Width", f"{handler.network.image.shape[0]} x {handler.network.image.shape[1]} x {handler.network.image.shape[2]}"],
                ["Dimensions", "3D"]
            ]
        else:
            image_props = [
                ["Name", f"{handler.path.name}"],
                ["Height x Width", f"{handler.network.image.shape[0]} x {handler.network.image.shape[1]}"],
                ["Dimensions", "2D"]
            ]

        self.imagePropsModel.reset_data(image_props)

    @Slot()
    def update_graph_model(self):
        """Update the graph properties model with the selected image's graph properties."""
        handler = self.file_controller.get_selected_handler()

        if handler is None:
            return

        if handler.graph_loaded:
            graph_props = [
                ["Edge Count", f"{handler.network.graph.ecount()}"],
                ["Node Count", f"{handler.network.graph.vcount()}"],
            ]

            for key, value in handler.properties.items():
                if value:
                    graph_props.append([key, f"{value:.5f}"])

            self.graphPropsModel.reset_data(graph_props)

    @Slot(str)
    def run_graph_analysis(self, options):
        """Compute selected graph properties of the selected image."""
        if self.wait_flag:
            logging.info(
                "Please Wait: Another Task Running!",
                extra={"user": "SGT Logs"},
            )
            self.showAlertSignal.emit("Please Wait", "Another Task Running!")
            return

        handler = self.file_controller.get_selected_handler()
        if handler is None:
            self.wait_flag = False
            return

        self.wait_flag = True
        options = json.loads(options)

        self.thread = QThreadWorker(
            self.worker_task.task_run_graph_analysis,
            (handler, options),
        )

        self.worker_task.taskFinishedSignal.connect(
            self._on_graph_analysis_finished
        )
        self.worker_task.taskFinishedSignal.connect(self.thread.quit)

        self.thread.start()

    @Slot(bool, object)
    def _on_graph_analysis_finished(self, success, result):
        self.wait_flag = False
        if success:
            self.update_graph_model()
        else:
            self.showAlertSignal.emit(
                "Graph Analysis Failed", "Error computing graph properties."
            )

    @Slot(result=str)
    def get_sgt_version(self):
        """"""
        # Copyright (C) 2024, the Regents of the University of Michigan.
        return f"StructuralGT v{__version__}"

    @Slot(result=str)
    def get_about_details(self):
        about_app = (
            f"A software tool that allows graph theory analysis of nano-structures. This is a modified version "
            "of StructuralGT initially proposed by Drew A. Vecchio, DOI: "
            "<html><a href='https://pubs.acs.org/doi/10.1021/acsnano.1c04711'>10.1021/acsnano.1c04711</a></html><html><br/><br/></html>"
            "Contributors:<html><br/></html>"
            "1. Nicolas Kotov<html><br/></html>"
            "2. Dickson Owuor<html><br/></html>"
            "3. Alain Kadar<html><br/><br/></html>"
            "Documentation:<html><br/></html>"
            "<html><a href='https://structuralgt.readthedocs.io'>structuralgt.readthedocs.io</a></html><html><br/><br/></html>"
            f"{self.get_sgt_version()}<html><br/></html>"
            "Copyright (C) 2018-2025, The Regents of the University of Michigan.<html><br/></html>"
            "License: GPL GNU v3<html><br/></html>"
        )
        return about_app

    @Slot(str, float, result=bool)
    def add_csv_data(self, csv_path, cutoff):
        """Load CSV data and create a PointNetwork object."""
        csv_path = self.verify_path(csv_path)
        if not csv_path:
            return False

        try:
            # Read CSV file using pandas
            df = pd.read_csv(csv_path)

            # Validate that CSV has coordinate columns
            required_columns = ["x", "y"]
            if not all(col in df.columns for col in required_columns):
                self.showAlertSignal.emit(
                    "CSV Format Error",
                    "CSV must contain at least 'x' and 'y' columns for coordinates.",
                )
                return False

            # Extract coordinate data
            if "z" in df.columns:
                positions = df[["x", "y", "z"]].values
            else:
                positions = df[["x", "y"]].values
                # Add z=0 column for 2D data
                positions = np.column_stack(
                    [positions, np.zeros(len(positions))]
                )

            # Create PointNetwork object
            point_network = PointNetwork(positions, cutoff)

            # Create a CSV handler similar to ImageHandler
            csv_handler = CSVHandler(csv_path, point_network)
            self.images.append(csv_handler)

            # Update the image list model
            self.imageListModel.reset_data(
                [
                    {
                        "id": i,
                        "name": str(
                            image.img_path.name
                            if hasattr(image, "img_path")
                            else f"CSV_{i}"
                        ),
                    }
                    for i, image in enumerate(self.images)
                ]
            )

            #self.load_image()
            return True

        except Exception as err:
            logging.exception(
                "CSV Loading Error: %s", err, extra={"user": "SGT Logs"}
            )
            self.showAlertSignal.emit(
                "CSV Error", f"Error loading CSV file: {str(err)}"
            )
            return False

    @Slot(str)
    def apply_binarizer_direct(self, options):
        """Apply binarizer by directly calling Network.binarize() method"""
        image = self.get_selected_image()
        if image is None:
            return

        try:
            # Parse the options from JSON
            if options:
                options_dict = json.loads(options)
            else:
                options_dict = None
            
            # Call Network.binarize() directly
            image.network.binarize(options_dict)
            
            # Update the display to show binary image
            image.binary_loaded = True
            image.display_type = "binary"
            self.load_image()
            
        except Exception as err:
            logging.exception(
                "Binarizer Error: %s", err, extra={"user": "SGT Logs"}
            )
            self.showAlertSignal.emit(
                "Binarizer Error", f"Error applying binarizer: {str(err)}"
            )
