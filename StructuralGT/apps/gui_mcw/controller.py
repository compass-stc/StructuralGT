import os
import sys
import json
import logging
import numpy as np
import pandas as pd
import tempfile
import shutil
from ovito import scene
from ovito.io import import_file
from ovito.vis import Viewport
from ovito.gui import create_qwidget
from typing import TYPE_CHECKING
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QObject, Signal, Slot

if TYPE_CHECKING:
    # False at run time, only for a type-checker
    from _typeshed import SupportsWrite

from .handler import NetworkHandler, PointNetworkHandler
from .csv_handler import CSVHandler
from .table_model import TableModel
from .list_model import ListModel
from .qthread_worker import QThreadWorker, WorkerTask

from StructuralGT import __version__
from StructuralGT.networks import PointNetwork

ALLOWED_IMG_EXTENSIONS = ["*.jpg", "*.jpeg", "*.tif", "*.tiff"]
ALLOWED_CSV_EXTENSIONS = ["*.csv"]


class MainController(QObject):
    """Exposes a method to refresh the image in QML"""

    # updateProgressSignal = Signal(int, str)
    # taskTerminatedSignal = Signal(bool, list)
    # projectOpenedSignal = Signal(str)
    # enableRectangularSelectionSignal = Signal(bool)
    # showCroppingToolSignal = Signal(bool)
    # showUnCroppingToolSignal = Signal(bool)
    # performCroppingSignal = Signal(bool)

    showAlertSignal = Signal(str, str)
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

        # Create network objects
        self.handlers = []
        self.selected_index = 0

        # Create QThreadWorker for long tasks
        self.wait_flag = False
        self.worker_task = WorkerTask()
        self.thread = QThreadWorker(None, None)

        # Create Models
        self.imagePropsModel = TableModel([])
        self.graphPropsModel = TableModel([])
        self.imageListModel = ListModel([])
        
        self.ovito_widget_opened = False

    @Slot(str, result=str)
    def get_file_extensions(self, option):
        if option == "img":
            pattern_string = " ".join(ALLOWED_IMG_EXTENSIONS)
            return f"Image files ({pattern_string})"
        elif option == "proj":
            return "Project files (*.sgtproj)"
        elif option == "csv":
            pattern_string = " ".join(ALLOWED_CSV_EXTENSIONS)
            return f"CSV files ({pattern_string})"
        else:
            return ""

    def verify_path(self, a_path):
        if not a_path:
            logging.info(
                "No folder/file selected.", extra={"user": "SGT Logs"}
            )
            self.showAlertSignal.emit(
                "File/Directory Error", "No folder/file selected."
            )
            return False

        # Convert QML "file:///" path format to a proper OS path
        if a_path.startswith("file:///"):
            if sys.platform.startswith("win"):
                # Windows Fix (remove extra '/')
                a_path = a_path[8:]
            else:
                # macOS/Linux (remove "file://")
                a_path = a_path[7:]

        # Normalize the path
        a_path = os.path.normpath(a_path)

        if not os.path.exists(a_path):
            logging.exception(
                "Path Error: %s", IOError, extra={"user": "SGT Logs"}
            )
            self.showAlertSignal.emit(
                "Path Error",
                f"File/Folder in {a_path} does not exist. Try again.",
            )
            return False
        return a_path

    def get_selected_handler(self):
        try:
            return self.handlers[self.selected_index]
        except IndexError:
            logging.info(
                "No Image Error: Please import/add an image.",
                extra={"user": "SGT Logs"},
            )
            self.showAlertSignal.emit(
                "No Image Error", "No image added! Please import/add an image."
            )
            return None

    @Slot(result=bool)
    def is_3d_img(self):
        """Check if the selected image is a 3D image."""
        if not self.handlers:
            return False
        handler = self.get_selected_handler()
        return isinstance(handler, NetworkHandler) and handler.dim == 3


    @Slot(result=bool)
    def graph_loaded(self):
        if self.handlers:
            return self.get_selected_handler().graph_loaded
        return False

    @Slot(result=str)
    def display_type(self):
        if not self.handlers:
            return "welcome"
        return self.get_selected_handler().display_type

    @Slot(result=int)
    def get_selected_slice_index(self):
        """Get the selected slice index of the selected image."""
        if not self.handlers:
            return -1
        return self.get_selected_handler().selected_slice_index

    @Slot(result=int)
    def get_number_of_slices(self):
        """Get the number of slices of the selected image."""
        return self.get_selected_handler().network.image.shape[0]

    @Slot(int, result=bool)
    def set_selected_slice_index(self, index):
        """Set the selected slice index of the selected image."""
        handler = self.get_selected_handler()
        if handler and 0 <= index < handler.network.image.shape[0]:
            handler.selected_slice_index = index
            self.load_image()
            return True
        return False

    @Slot(result=bool)
    def load_prev_slice(self):
        """Load the previous slice of the selected image."""
        handler = self.get_selected_handler()
        if handler and handler.selected_slice_index > 0:
            handler.selected_slice_index -= 1
            self.load_image()
            return True
        return False

    @Slot(result=bool)
    def load_next_slice(self):
        """Load the next slice of the selected image."""
        handler = self.get_selected_handler()
        if handler and handler.selected_slice_index < handler.network.image.shape[0] - 1:
            handler.selected_slice_index += 1
            self.load_image()
            return True
        return False

    def create_handler(self, path, type):
        path = self.verify_path(path)
        if not path:
            return False
        print(path)

        # Try reading the image
        try:
            if type == "3D":
                # Create a 3D image object
                self.handlers.append(NetworkHandler(path, dim=3))
            elif type == "2D":
                # Create a temporary directory for the image
                prefix = "sgt_"
                temp_dir = tempfile.TemporaryDirectory(prefix=prefix)

                # Copy the image to the temporary directory
                temp_path = os.path.join(
                    temp_dir.name, os.path.basename(path)
                )
                shutil.copy(path, temp_path)

                print(temp_dir.name)

                if type == "2D":
                    # Create a 2d image object
                    self.handlers.append(NetworkHandler(temp_dir, dim=2))
            elif type == "Point":
                self.handlers.append(PointNetworkHandler(path, cutoff=1200))
            return True

        except Exception as err:
            logging.exception(
                "File Error: %s", err, extra={"user": "SGT Logs"}
            )
            self.showAlertSignal.emit(
                "File Error", "Error processing image. Try again."
            )
            return False

    # TODO: make it compatible with point network
    @Slot(str, str, result=bool)
    def add_handler(self, img_path, type):
        """Verify and validate an image path, use it to create an Network and load it in view."""
        is_created = self.create_handler(img_path, type)
        if is_created:

            self.imageListModel.reset_data(
                [{"id": i, "name": str(handler.path)}
                for i, handler in enumerate(self.handlers)]
            )

            if isinstance(self.get_selected_handler(), NetworkHandler):
                self.load_image()
            else:
                self.load_graph()

            return True
        return False

    @Slot(int, result=bool)
    def delete_handler(self, index):
        """Delete an image from the list of images."""
        # Remove the image from the list
        del self.handlers[index]
        self.selected_index = 0 if not self.handlers else min(
            self.selected_index, len(self.handlers) - 1
        )

        # Reset the models
        self.imageListModel.reset_data(
            [{"id": i, "name": str(handler.path)}
                for i, handler in enumerate(self.handlers)]
        )

        return True

    @Slot(int)
    def load_image(self, index=None):
        """Load the image of the selected network handler."""
        print("Loading image...")
        try:
            if index is not None:
                if index == self.selected_index:
                    return
                else:
                    self.selected_index = index

            self.changeImageSignal.emit()
        except Exception as err:
            self.delete_handler(self.selected_index)
            self.selected_index = 0
            logging.exception(
                "Image Loading Error: %s", err, extra={"user": "SGT Logs"}
            )
            self.showAlertSignal.emit(
                "Image Error", "Error loading image. Try again."
            )

    @Slot(result=str)
    def get_pixmap(self):
        """Returns the URL that QML should use to load the image"""
        curr_img_view = np.random.randint(0, 4)
        unique_num = (
            self.selected_index
            + curr_img_view
            + np.random.randint(low=21, high=1000)
        )
        return "image://imageProvider/" + str(unique_num)

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

        handler = self.get_selected_handler()
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

        handler = self.get_selected_handler()
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

        image = self.get_selected_handler()

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
                handler = self.get_selected_handler()
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
        handler = self.get_selected_handler()

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
        handler = self.get_selected_handler()

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

        handler = self.get_selected_handler()
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
