
import os
import sys
import pickle
import logging
import requests
import numpy as np
from packaging import version
from ovito import scene
from ovito.vis import Viewport
from ovito.io import import_file
from ovito.gui import create_qwidget
from typing import TYPE_CHECKING, Optional
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject,Signal,Slot

if TYPE_CHECKING:
    # False at run time, only for a type-checker
    from _typeshed import SupportsWrite

from .tree_model import TreeModel
from .table_model import TableModel
from .checkbox_model import CheckBoxModel
from .imagegrid_model import ImageGridModel
from .qthread_worker import QThreadWorker, WorkerTask

from ... import __version__
from ...utils.sgt_utils import img_to_base64, verify_path
from ...imaging.image_processor import ImageProcessor, FiberNetworkBuilder, ALLOWED_IMG_EXTENSIONS
from ...compute.graph_analyzer import GraphAnalyzer#, COMPUTING_DEVICE


class MainController(QObject):
    """Exposes a method to refresh the image in QML"""

    showAlertSignal = Signal(str, str)
    errorSignal = Signal(str)
    updateProgressSignal = Signal(int, str)
    taskTerminatedSignal = Signal(bool, list)
    projectOpenedSignal = Signal(str)
    changeImageSignal = Signal()
    imageChangedSignal = Signal()
    enableRectangularSelectionSignal = Signal(bool)
    showCroppingToolSignal = Signal(bool)
    showUnCroppingToolSignal = Signal(bool)
    performCroppingSignal = Signal(bool)

    def __init__(self, qml_app: QApplication):
        super().__init__()
        self.qml_app = qml_app
        self.img_loaded = False
        self.project_open = False
        self.allow_auto_scale = True

        # Project data
        self.project_data = {"name": "", "file_path": ""}

        # Initialize flags
        self.wait_flag = False

        # Create graph objects
        self.sgt_objs = {}
        self.selected_sgt_obj_index = 0

        # Create Models
        self.imgThumbnailModel = TableModel([])
        self.imagePropsModel = TableModel([])
        self.graphPropsModel = TableModel([])
        self.graphComputeModel = TableModel([])
        self.microscopyPropsModel = CheckBoxModel([])

        self.gteTreeModel = TreeModel([])
        self.gtcListModel = CheckBoxModel([])
        self.exportGraphModel = CheckBoxModel([])
        self.imgBatchModel = CheckBoxModel([])
        self.imgControlModel = CheckBoxModel([])
        self.imgBinFilterModel = CheckBoxModel([])
        self.imgFilterModel = CheckBoxModel([])
        self.imgScaleOptionModel = CheckBoxModel([])
        self.saveImgModel = CheckBoxModel([])
        self.img3dGridModel = ImageGridModel([], set([]))

        # Create QThreadWorker for long tasks
        self.worker = QThreadWorker(0, None)
        self.worker_task = WorkerTask()

    def update_img_models(self, sgt_obj: GraphAnalyzer):
        """
            Reload image configuration selections and controls from saved dict to QML gui_mcw after the image is loaded.

            :param sgt_obj: A GraphAnalyzer object with all saved user-selected configurations.
        """
        try:
            ntwk_p = sgt_obj.ntwk_p
            sel_img_batch = ntwk_p.get_selected_batch()
            first_index = next(iter(sel_img_batch.selected_images), None)  # 1st selected image
            first_index = first_index if first_index is not None else 0  # first image if None
            options_img = sel_img_batch.images[first_index].configs

            img_controls = [v for v in options_img.values() if v["type"] == "image-control"]
            bin_filters = [v for v in options_img.values() if v["type"] == "binary-filter"]
            img_filters = [v for v in options_img.values() if v["type"] == "image-filter"]
            img_properties = [v for v in options_img.values() if v["type"] == "image-property"]
            file_options = [v for v in options_img.values() if v["type"] == "file-options"]
            options_scaling = sel_img_batch.scaling_options
            batch_list = [{"id": f"batch_{i}", "text": f"Image Batch {i+1}", "value": i}
                          for i in range(len(sgt_obj.ntwk_p.image_batches))]

            self.imgBatchModel.reset_data(batch_list)
            self.imgScaleOptionModel.reset_data(options_scaling)

            self.imgControlModel.reset_data(img_controls)
            self.imgBinFilterModel.reset_data(bin_filters)
            self.imgFilterModel.reset_data(img_filters)
            self.microscopyPropsModel.reset_data(img_properties)
            self.saveImgModel.reset_data(file_options)
        except Exception as err:
            logging.exception("Fatal Error: %s", err, extra={'user': 'SGT Logs'})
            self.showAlertSignal.emit("Fatal Error", "Error re-loading image configurations! Close app and try again.")

    def update_graph_models(self, sgt_obj: GraphAnalyzer):
        """
            Reload graph configuration selections and controls from saved dict to QML gui_mcw.
        Args:
            sgt_obj: a GraphAnalyzer object with all saved user-selected configurations.

        Returns:

        """
        try:
            ntwk_p = sgt_obj.ntwk_p
            sel_img_batch = ntwk_p.get_selected_batch()
            graph_obj = sel_img_batch.graph_obj
            option_gte = graph_obj.configs
            options_gtc = sgt_obj.configs

            graph_options = [v for v in option_gte.values() if v["type"] == "graph-extraction"]
            file_options = [v for v in option_gte.values() if v["type"] == "file-options"]

            self.gteTreeModel.reset_data(graph_options)
            self.exportGraphModel.reset_data(file_options)
            self.gtcListModel.reset_data(list(options_gtc.values()))

            self.imagePropsModel.reset_data(sel_img_batch.props)
            self.graphPropsModel.reset_data(graph_obj.props)
            self.graphComputeModel.reset_data(sgt_obj.props)
        except Exception as err:
            logging.exception("Fatal Error: %s", err, extra={'user': 'SGT Logs'})
            self.showAlertSignal.emit("Fatal Error", "Error re-loading image configurations! Close app and try again.")

    def get_selected_sgt_obj(self):
        try:
            keys_list = list(self.sgt_objs.keys())
            key_at_index = keys_list[self.selected_sgt_obj_index]
            sgt_obj = self.sgt_objs[key_at_index]
            return sgt_obj
        except IndexError:
            logging.info("No Image Error: Please import/add an image.", extra={'user': 'SGT Logs'})
            # self.showAlertSignal.emit("No Image Error", "No image added! Please import/add an image.")
            return None

    def create_sgt_object(self, img_path):
        """
        A function that processes a selected image file and creates an analyzer object with default configurations.

        Args:
            img_path: file path to image

        Returns:
        """

        success, result = verify_path(img_path)
        if success:
            img_path = result
        else:
            logging.info(result, extra={'user': 'SGT Logs'})
            self.showAlertSignal.emit("File/Directory Error", result)
            return False

        # Create an SGT object as a GraphAnalyzer object.
        try:
            ntwk_p, img_file = ImageProcessor.create_imp_object(img_path, config_file="", allow_auto_scale=self.allow_auto_scale)
            sgt_obj = GraphAnalyzer(ntwk_p)

            # Store the StructuralGT object and sync application
            self.sgt_objs[img_file] = sgt_obj
            self.update_img_models(self.get_selected_sgt_obj())
            self.update_graph_models(self.get_selected_sgt_obj())
            return True
        except Exception as err:
            logging.exception("File Error: %s", err, extra={'user': 'SGT Logs'})
            self.showAlertSignal.emit("File Error", "Error processing image. Try again.")
            return False

    def delete_sgt_object(self, index=None):
        """
        Delete SGT Obj stored at the specified index (if not specified, get the current index).
        """
        del_index = index if index is not None else self.selected_sgt_obj_index
        if 0 <= del_index < len(self.sgt_objs):  # Check if the index exists
            keys_list = list(self.sgt_objs.keys())
            key_at_del_index = keys_list[self.selected_sgt_obj_index]
            # Delete the object at index
            del self.sgt_objs[key_at_del_index]
            # Update Data
            img_list, img_cache = self.get_thumbnail_list()
            self.imgThumbnailModel.update_data(img_list, img_cache)
            self.selected_sgt_obj_index = 0
            self.load_image(reload_thumbnails=True)
            self.imageChangedSignal.emit()

    def save_project_data(self):
        """
        A handler function that handles saving project data.
        Returns: True if successful, False otherwise.

        """
        if not self.project_open:
            return False
        try:
            file_path = self.project_data["file_path"]
            with open(file_path, 'wb') as project_file:  # type: Optional[SupportsWrite[bytes]]
                pickle.dump(self.sgt_objs, project_file)
            return True
        except Exception as err:
            logging.exception("Project Saving Error: %s", err, extra={'user': 'SGT Logs'})
            self.showAlertSignal.emit("Save Error", "Unable to save project data. Close app and try again.")
            return False

    def get_thumbnail_list(self):
        """
        Get names and base64 data of images to be used in Project List thumbnails.
        """
        keys_list = list(self.sgt_objs.keys())
        if len(keys_list) <= 0:
            return None, None
        item_data = []
        image_cache = {}
        for key in keys_list:
            item_data.append([key])  # Store the key
            sgt_obj = self.sgt_objs[key]
            ntwk_p = sgt_obj.ntwk_p
            sel_img_batch = ntwk_p.get_selected_batch()
            img_cv = sel_img_batch.images[0].img_2d  # First image, assuming OpenCV image format
            base64_data = img_to_base64(img_cv)
            image_cache[key] = base64_data  # Store base64 string
        return item_data, image_cache

    def get_selected_images(self, img_view: str = None):
        """
        Get selected images from a specific image batch.
        """
        sgt_obj = self.get_selected_sgt_obj()
        ntwk_p = sgt_obj.ntwk_p
        sel_img_batch = ntwk_p.get_selected_batch()
        sel_images = [sel_img_batch.images[i] for i in sel_img_batch.selected_images]
        if img_view is not None:
            sel_img_batch.current_view = img_view
        return sel_images

    def _handle_progress_update(self, progress_val: int, msg: str):
        """
        Handler function for progress updates for ongoing tasks.
        Args:
            progress_val: Progress value, range is 0-100%.
            msg: Progress message to be displayed.

        Returns:

        """

        if 0 <= progress_val <= 100:
            self.updateProgressSignal.emit(progress_val, msg)
            logging.info(f"{progress_val}%: {msg}", extra={'user': 'SGT Logs'})
        elif progress_val > 100:
            self.updateProgressSignal.emit(progress_val, msg)
            logging.info(f"{msg}", extra={'user': 'SGT Logs'})
        else:
            logging.exception("Error: %s", msg, extra={'user': 'SGT Logs'})
            self.errorSignal.emit(msg)

    def _handle_finished(self, success_val: bool, result: None | list | FiberNetworkBuilder | GraphAnalyzer):
        """
        Handler function for sending updates/signals on termination of tasks.
        Args:
            success_val:
            result:

        Returns:

        """
        self.wait_flag = False
        if not success_val:
            if type(result) is list:
                logging.info(result[0] + ": " + result[1], extra={'user': 'SGT Logs'})
                self.taskTerminatedSignal.emit(success_val, result)
            elif type(result) is GraphAnalyzer:
                pdf_saved = GraphAnalyzer.write_to_pdf(result, self._handle_progress_update)
                if pdf_saved:
                    self._handle_finished(True, result)
        else:
            if type(result) is ImageProcessor:
                self._handle_progress_update(100, "Graph extracted successfully!")
                sgt_obj = self.get_selected_sgt_obj()
                sgt_obj.ntwk_p = result

                # Load the graph image to the app
                self.changeImageSignal.emit()

                # Send task termination signal to QML
                self.taskTerminatedSignal.emit(success_val, [])
            elif type(result) is GraphAnalyzer:
                self._handle_progress_update(100, "GT PDF successfully generated!")
                # Update graph properties
                self.update_graph_models(self.get_selected_sgt_obj())
                # Send task termination signal to QML
                self.taskTerminatedSignal.emit(True, ["GT calculations completed", "The image's GT parameters have been "
                                                                                "calculated. Check out generated PDF in "
                                                                                "'Output Dir'."])
            elif type(result) is dict:
                self._handle_progress_update(100, "All GT PDF successfully generated!")
                # Update graph properties
                self.update_graph_models(self.get_selected_sgt_obj())
                # Send task termination signal to QML
                self.taskTerminatedSignal.emit(True, ["All GT calculations completed", "GT parameters of all "
                                                                                    "images have been calculated. Check "
                                                                                    "out all the generated PDFs in "
                                                                                    "'Output Dir'."])
            else:
                self.taskTerminatedSignal.emit(success_val, [])

    @Slot(result=str)
    def get_sgt_version(self):
        """"""
        # Copyright (C) 2024, the Regents of the University of Michigan.
        # return f"StructuralGT v{__version__}, Computing: {COMPUTING_DEVICE}"
        return f"v{__version__}"

    @Slot(result=str)
    def get_about_details(self):
        about_app = (
            "<html>"
            "<p>"
            "A software tool for performing Graph Theory analysis on <br>microscopy images. This is a modified version "
            "of StructuralGT <br>initially proposed by Drew A. Vecchio,<br>"
            "<b>DOI:</b> <a href='https://pubs.acs.org/doi/10.1021/acsnano.1c04711'>10.1021/acsnano.1c04711</a>"
            "</p><p>"
            "<b>Main Contributors:</b><br>"
            "<table border='0.5' cellspacing='0' cellpadding='4'>"
            # "<tr><th>Name</th><th>Email</th></tr>"
            "<tr><td>Dickson Owuor</td><td>owuor@umich.edu</td></tr>"
            "<tr><td>Nicolas Kotov</td><td>kotov@umich.edu</td></tr>"
            "<tr><td>Alain Kadar</td><td>alaink@umich.edu</td></tr>"
            "<tr><td>Xiong Ye Xiao</td><td>xiongyex@usc.edu</td></tr>"
            "<tr><td>Kotov Lab</td><td></td></tr>"
            "<tr><td>COMPASS</td><td></td></tr>"
            "</table></p><p><br><br>"
            "<b>Documentation:</b> <a href='https://structural-gt.readthedocs.io'>structural-gt.readthedocs.io</a>"
            "<br>"
            f"<b> Version: </b> {self.get_sgt_version()}<br>"
            "<b>License:</b> GPL GNU v3"
            "</p><p>"
            "Copyright (C) 2018-2025<br>The Regents of the University of Michigan."
            "</p>"
            "</html>")
        return about_app

    @Slot(result=str)
    def check_for_updates(self):
        """"""
        github_url = "https://raw.githubusercontent.com/owuordickson/structural-gt/refs/heads/main/src/StructuralGT/__init__.py"

        try:
            response = requests.get(github_url, timeout=5)
            response.raise_for_status()
        except requests.RequestException as e:
            msg = f"Error checking for updates: {e}"
            return msg

        remote_version = None
        for line in response.text.splitlines():
            if line.strip().startswith("__install_version__"):
                try:
                    remote_version = line.split("=")[1].strip().strip("\"'")
                    break
                except IndexError:
                    msg = "Could not connect to server!"
                    return msg

        if not remote_version:
            msg = "Could not find the new version!"
            return msg

        new_version = version.parse(remote_version)
        current_version = version.parse(__version__)
        if new_version > current_version:
            # https://github.com/owuordickson/structural-gt/releases/tag/v3.3.5
            msg = (
                "New version available!<br>"
                f"Download via this <a href='https://github.com/owuordickson/structural-gt/releases/tag/v{remote_version}'>link</a>"
            )
        else:
            msg = "No updates available."
        return msg

    @Slot(str, result=str)
    def get_file_extensions(self, option):
        if option == "img":
            pattern_string = ' '.join(ALLOWED_IMG_EXTENSIONS)
            return f"Image files ({pattern_string})"
        elif option == "proj":
            return "Project files (*.sgtproj)"
        else:
            return ""

    @Slot(result=str)
    def get_pixmap(self):
        """Returns the URL that QML should use to load the image"""
        curr_img_view = np.random.randint(0, 4)
        unique_num = self.selected_sgt_obj_index + curr_img_view + np.random.randint(low=21, high=1000)
        return "image://imageProvider/" + str(unique_num)

    @Slot(result=bool)
    def is_img_3d(self):
        sgt_obj = self.get_selected_sgt_obj()
        if sgt_obj is None:
            return False
        sel_img_batch = sgt_obj.ntwk_p.get_selected_batch()
        is_3d = not sel_img_batch.is_2d
        return is_3d

    @Slot(result=int)
    def get_selected_img_batch(self):
        sgt_obj = self.get_selected_sgt_obj()
        return sgt_obj.ntwk_p.selected_batch

    @Slot(result=str)
    def get_selected_img_type(self):
        sgt_obj = self.get_selected_sgt_obj()
        sel_img_batch = sgt_obj.ntwk_p.get_selected_batch()
        return sel_img_batch.current_view

    @Slot(result=str)
    def get_img_nav_location(self):
        return f"{(self.selected_sgt_obj_index + 1)} / {len(self.sgt_objs)}"

    @Slot(result=str)
    def get_output_dir(self):
        sgt_obj = self.get_selected_sgt_obj()
        if sgt_obj is None:
            return ""
        return f"{sgt_obj.ntwk_p.output_dir}"

    @Slot(result=bool)
    def get_auto_scale(self):
        return self.allow_auto_scale

    @Slot(int)
    def delete_selected_thumbnail(self, img_index):
        """Delete the selected image from the list."""
        self.delete_sgt_object(img_index)

    @Slot(str)
    def set_output_dir(self, folder_path):

        # Convert QML "file:///" path format to a proper OS path
        if folder_path.startswith("file:///"):
            if sys.platform.startswith("win"):  # Windows Fix (remove extra '/')
                folder_path = folder_path[8:]
            else:  # macOS/Linux (remove "file://")
                folder_path = folder_path[7:]
        folder_path = os.path.normpath(folder_path)  # Normalize the path

        # Update for all sgt_objs
        key_list = list(self.sgt_objs.keys())
        for key in key_list:
            sgt_obj = self.sgt_objs[key]
            sgt_obj.ntwk_p.output_dir = folder_path
        self.imageChangedSignal.emit()

    @Slot(bool)
    def set_auto_scale(self, auto_scale):
        """Set the auto-scale parameter for each image."""
        self.allow_auto_scale = auto_scale

    @Slot(int)
    def select_img_batch(self, batch_index=-1):
        if batch_index < 0:
            return

        try:
            sgt_obj = self.get_selected_sgt_obj()
            sgt_obj.ntwk_p.select_image_batch(batch_index)
            self.update_img_models(sgt_obj)
            self.changeImageSignal.emit()
        except Exception as err:
            logging.exception("Batch Change Error: %s", err, extra={'user': 'SGT Logs'})
            self.showAlertSignal.emit("Image Batch Error", f"Error encountered while trying to access batch "
                                                           f"{batch_index}. Restart app and try again.")

    @Slot(int, bool)
    def toggle_selected_batch_image(self, img_index, selected):
        sgt_obj = self.get_selected_sgt_obj()
        sel_img_batch = sgt_obj.ntwk_p.get_selected_batch()
        if selected:
            sel_img_batch.selected_images.add(img_index)
        else:
            sel_img_batch.selected_images.discard(img_index)
        self.changeImageSignal.emit()

    @Slot(str)
    def toggle_current_img_view(self, choice: str = None):
        """
            Change the view of the current image to either: original, binary, processed or graph.

            :param choice: Selected view to be loaded.
        """
        sgt_obj = self.get_selected_sgt_obj()
        if sgt_obj is None:
            return
        sel_img_batch = sgt_obj.ntwk_p.get_selected_batch()
        if choice is not None:
            sel_img_batch.current_view = choice
        self.changeImageSignal.emit()

    @Slot(bool)
    def reload_graph_image(self, only_giant_graph=False):
        sgt_obj = self.get_selected_sgt_obj()
        sel_img_batch = sgt_obj.ntwk_p.get_selected_batch()
        sgt_obj.ntwk_p.draw_graph_image(sel_img_batch, show_giant_only=only_giant_graph)
        self.changeImageSignal.emit()

    @Slot()
    def load_graph_simulation(self):
        """Render and visualize OVITO graph network simulation."""
        try:
            # Clear any existing scene
            for p_line in list(scene.pipelines):
                p_line.remove_from_scene()

            # Create OVITO data pipeline
            sgt_obj = self.get_selected_sgt_obj()
            sel_batch = sgt_obj.ntwk_p.get_selected_batch()
            pipeline = import_file(sel_batch.graph_obj.gsd_file)
            pipeline.add_to_scene()

            vp = Viewport(type=Viewport.Type.Perspective, camera_dir=(2, 1, -1))
            ovito_widget = create_qwidget(vp, parent=self.qml_app.activeWindow())
            ovito_widget.setMinimumSize(800, 500)
            vp.zoom_all((800, 500))
            ovito_widget.show()

            """
            # Find the QML Rectangle to embed into
            root = self.qml_engine.rootObjects()[0]
            ntwk_container = root.findChild(QObject, "ntwkContainer")

            if ntwk_container:
                # Testing
                # print(f"Found it! {type(ntwk_container)}")
                # ntwk_container.setProperty("color", "#8b0000")

                # Grab rectangle properties
                x = ntwk_container.property("x")
                y = ntwk_container.property("y")
                w = ntwk_container.property("width")
                h = ntwk_container.property("height")

                # Create OVITO data pipeline
                sgt_obj = self.get_selected_sgt_obj()
                filename, out_dir = sgt_obj.ntwk_p.get_filenames()
                gsd_filename = filename + "_skel.gsd"
                gsd_file = str(os.path.join(out_dir, gsd_filename))
                pipeline = import_file(gsd_file)
                pipeline.add_to_scene()

                vp = Viewport(type=Viewport.Type.Perspective, camera_dir=(2, 1, -1))
                ovito_widget = create_qwidget(vp, parent=self.qml_app.activeWindow())
                ovito_widget.setMinimumSize(800, 500)
                vp.zoom_all((800, 500))

                # Re-parent OVITO QWidget
                ovito_widget.setGeometry(x, y, w, h)
                ovito_widget.show()"""
        except Exception as e:
            print("Graph Simulation Error:", e)

    @Slot(int)
    def load_image(self, index=None, reload_thumbnails=False):
        try:
            if index is not None:
                if index == self.selected_sgt_obj_index:
                    return
                else:
                    self.selected_sgt_obj_index = index

            if reload_thumbnails:
                # Update the thumbnail list data (delete/add image)
                img_list, img_cache = self.get_thumbnail_list()
                self.imgThumbnailModel.update_data(img_list, img_cache)

            # Load the SGT Object data of the selected image
            self.update_img_models(self.get_selected_sgt_obj())
            self.imgThumbnailModel.set_selected(self.selected_sgt_obj_index)
            self.changeImageSignal.emit()
        except Exception as err:
            self.delete_sgt_object()
            self.selected_sgt_obj_index = 0
            logging.exception("Image Loading Error: %s", err, extra={'user': 'SGT Logs'})
            self.showAlertSignal.emit("Image Error", "Error loading image. Try again.")

    @Slot(result=bool)
    def load_prev_image(self):
        """Load the previous image in the list into view."""
        if self.selected_sgt_obj_index > 0:
            self.selected_sgt_obj_index = self.selected_sgt_obj_index - 1
            self.load_image()
            return True
        return False

    @Slot(result=bool)
    def load_next_image(self):
        """Load the next image in the list into view."""
        if self.selected_sgt_obj_index < (len(self.sgt_objs) - 1):
            self.selected_sgt_obj_index = self.selected_sgt_obj_index + 1
            self.load_image()
            return True
        return False

    @Slot()
    def apply_img_ctrl_changes(self):
        """Retrieve settings from the model and send to Python."""
        try:
            sel_images = self.get_selected_images(img_view='processed')
            if len(sel_images) <= 0:
                return
            for val in self.imgControlModel.list_data:
                for img in sel_images:
                    img.configs[val["id"]]["value"] = val["value"]
            self.changeImageSignal.emit()
        except Exception as err:
            logging.exception("Unable to Adjust Brightness/Contrast: " + str(err), extra={'user': 'SGT Logs'})
            self.taskTerminatedSignal.emit(False, ["Unable to Adjust Brightness/Contrast", 
                                                   "Error trying to adjust image brightness/contrast.Try again."])

    @Slot()
    def apply_microscopy_props_changes(self):
        """Retrieve settings from the model and send to Python."""
        try:
            sel_images = self.get_selected_images()
            if len(sel_images) <= 0:
                return
            for val in self.microscopyPropsModel.list_data:
                for img in sel_images:
                    img.configs[val["id"]]["value"] = val["value"]
                    img.get_pixel_width()
        except Exception as err:
            logging.exception("Unable to Update Microscopy Property Values: " + str(err), extra={'user': 'SGT Logs'})
            self.taskTerminatedSignal.emit(False, ["Unable to Update Microscopy Values",
                                                   "Error trying to update microscopy property values.Try again."])

    @Slot()
    def apply_img_bin_changes(self):
        """Retrieve settings from the model and send to Python."""
        try:
            sel_images = self.get_selected_images()
            if len(sel_images) <= 0:
                return
            for val in self.imgBinFilterModel.list_data:
                for img in sel_images:
                    img.configs[val["id"]]["value"] = val["value"]
            self.changeImageSignal.emit()
        except Exception as err:
            logging.exception("Apply Binary Image Filters: " + str(err), extra={'user': 'SGT Logs'})
            self.taskTerminatedSignal.emit(False, ["Unable to Apply Binary Filters", "Error while tying to apply "
                                                                                     "binary filters to image. Try again."])

    @Slot()
    def apply_img_filter_changes(self):
        """Retrieve settings from the model and send to Python."""
        try:
            sel_images = self.get_selected_images()
            if len(sel_images) <= 0:
                return
            for val in self.imgFilterModel.list_data:
                for img in sel_images:
                    img.configs[val["id"]]["value"] = val["value"]
                    try:
                        img.configs[val["id"]]["dataValue"] = val["dataValue"]
                    except KeyError:
                        pass
            self.changeImageSignal.emit()
        except Exception as err:
            logging.exception("Apply Image Filters: " + str(err), extra={'user': 'SGT Logs'})
            self.taskTerminatedSignal.emit(False, ["Unable to Apply Image Filters", "Error while tying to apply "
                                                                                    "image filters. Try again."])

    @Slot()
    def apply_img_scaling(self):
        """Retrieve settings from the model and send to Python."""
        try:
            self.set_auto_scale(True)
            sgt_obj = self.get_selected_sgt_obj()
            sgt_obj.ntwk_p.auto_scale = self.allow_auto_scale
            sel_img_batch = sgt_obj.ntwk_p.get_selected_batch()
            sel_img_batch.scaling_options = self.imgScaleOptionModel.list_data
            sgt_obj.ntwk_p.apply_img_scaling()
            self.changeImageSignal.emit()
        except Exception as err:
            logging.exception("Apply Image Scaling: " + str(err), extra={'user': 'SGT Logs'})
            self.taskTerminatedSignal.emit(False, ["Unable to Rescale Image", "Error while tying to re-scale "
                                                                              "image. Try again."])

    @Slot()
    def export_graph_to_file(self):
        """Export graph data and save as a file."""
        try:
            sel_images = self.get_selected_images()
            if len(sel_images) <= 0:
                return

            # 1. Get filename
            sgt_obj = self.get_selected_sgt_obj()
            ntwk_p = sgt_obj.ntwk_p
            filename, out_dir = ntwk_p.get_filenames()

            # 2. Update values
            sel_img_batch = ntwk_p.get_selected_batch()
            for val in self.exportGraphModel.list_data:
                sel_img_batch.graph_obj.configs[val["id"]]["value"] = val["value"]

            # 3. Save graph data to the file
            sel_img_batch.graph_obj.save_graph_to_file(filename, out_dir)
            self.taskTerminatedSignal.emit(True, ["Exporting Graph", "Exported files successfully stored in 'Output Dir'"])
        except Exception as err:
            logging.exception("Unable to Export Graph: " + str(err), extra={'user': 'SGT Logs'})
            self.taskTerminatedSignal.emit(False, ["Unable to Export Graph", "Error exporting graph to file. Try again."])

    @Slot()
    def save_img_files(self):
        """Retrieve and save images to the file."""
        try:

            sel_images = self.get_selected_images()
            if len(sel_images) <= 0:
                return
            for val in self.saveImgModel.list_data:
                for img in sel_images:
                    img.configs[val["id"]]["value"] = val["value"]
            sgt_obj = self.get_selected_sgt_obj()
            sgt_obj.ntwk_p.save_images_to_file()
            self.taskTerminatedSignal.emit(True,
                                           ["Save Images", "Image files successfully saved in 'Output Dir'"])
        except Exception as err:
            logging.exception("Unable to Save Image Files: " + str(err), extra={'user': 'SGT Logs'})
            self.taskTerminatedSignal.emit(False,
                                           ["Unable to Save Image Files", "Error saving images to file. Try again."])

    @Slot()
    def run_extract_graph(self):
        """Retrieve settings from the model and send to Python."""

        if self.wait_flag:
            logging.info("Please Wait: Another Task Running!", extra={'user': 'SGT Logs'})
            self.showAlertSignal.emit("Please Wait", "Another Task Running!")
            return

        self.worker_task = WorkerTask()
        try:
            self.wait_flag = True
            sgt_obj = self.get_selected_sgt_obj()

            self.worker = QThreadWorker(func=self.worker_task.task_extract_graph, args=(sgt_obj.ntwk_p,))
            self.worker_task.inProgressSignal.connect(self._handle_progress_update)
            self.worker_task.taskFinishedSignal.connect(self._handle_finished)
            self.worker.start()
        except Exception as err:
            self.wait_flag = False
            logging.exception("Graph Extraction Error: %s", err, extra={'user': 'SGT Logs'})
            self._handle_progress_update(-1, "Fatal error occurred! Close the app and try again.")
            self._handle_finished(False, ["Graph Extraction Error",
                                                          "Fatal error while trying to extract graph. "
                                                          "Close the app and try again."])

    @Slot()
    def run_graph_analyzer(self):
        """Retrieve settings from the model and send to Python."""
        if self.wait_flag:
            logging.info("Please Wait: Another Task Running!", extra={'user': 'SGT Logs'})
            self.showAlertSignal.emit("Please Wait", "Another Task Running!")
            return

        self.worker_task = WorkerTask()
        try:
            self.wait_flag = True
            sgt_obj = self.get_selected_sgt_obj()

            self.worker = QThreadWorker(func=self.worker_task.task_compute_gt, args=(sgt_obj,))
            self.worker_task.inProgressSignal.connect(self._handle_progress_update)
            self.worker_task.taskFinishedSignal.connect(self._handle_finished)
            self.worker.start()
        except Exception as err:
            self.wait_flag = False
            logging.exception("GT Computation Error: %s", err, extra={'user': 'SGT Logs'})
            self._handle_progress_update(-1, "Fatal error occurred! Close the app and try again.")
            self._handle_finished(False, ["GT Computation Error",
                                                          "Fatal error while trying calculate GT parameters. "
                                                          "Close the app and try again."])

    @Slot()
    def run_multi_graph_analyzer(self):
        """"""
        if self.wait_flag:
            logging.info("Please Wait: Another Task Running!", extra={'user': 'SGT Logs'})
            self.showAlertSignal.emit("Please Wait", "Another Task Running!")
            return

        self.worker_task = WorkerTask()
        try:
            self.wait_flag = True

            # Update Configs
            current_sgt_obj = self.get_selected_sgt_obj()
            keys_list = list(self.sgt_objs.keys())
            key_at_current = keys_list[self.selected_sgt_obj_index]
            shared_configs = current_sgt_obj.configs
            for key in keys_list:
                if key != key_at_current:
                    s_obj = self.sgt_objs[key]
                    s_obj.configs = shared_configs

            self.worker = QThreadWorker(func=self.worker_task.task_compute_multi_gt, args=(self.sgt_objs,))
            self.worker_task.inProgressSignal.connect(self._handle_progress_update)
            self.worker_task.taskFinishedSignal.connect(self._handle_finished)
            self.worker.start()
        except Exception as err:
            self.wait_flag = False
            logging.exception("GT Computation Error: %s", err, extra={'user': 'SGT Logs'})
            self._handle_progress_update(-1, "Fatal error occurred! Close the app and try again.")
            self._handle_finished(False, ["GT Computation Error",
                                                          "Fatal error while trying calculate GT parameters. "
                                                          "Close the app and try again."])

    @Slot(result=bool)
    def run_save_project(self):
        """"""
        if self.wait_flag:
            logging.info("Please Wait: Another Task Running!", extra={'user': 'SGT Logs'})
            self.showAlertSignal.emit("Please Wait", "Another Task Running!")
            return False

        self.wait_flag = True
        success_val = self.save_project_data()
        self.wait_flag = False
        return success_val

    @Slot(result=bool)
    def display_image(self):
        return self.img_loaded

    @Slot(result=bool)
    def display_graph(self):
        if len(self.sgt_objs) <= 0:
            return False

        sgt_obj = self.get_selected_sgt_obj()
        sel_img_batch = sgt_obj.ntwk_p.get_selected_batch()
        if sel_img_batch.graph_obj.img_ntwk is None:
            return False

        if sel_img_batch.current_view  == "graph":
            return True
        return False

    @Slot(result=bool)
    def image_batches_exist(self):
        if not self.img_loaded:
            return False

        sgt_obj = self.get_selected_sgt_obj()
        batch_count = len(sgt_obj.ntwk_p.image_batches)
        batches_exist = True if batch_count > 1 else False
        return batches_exist

    @Slot(result=bool)
    def is_project_open(self):
        return self.project_open

    @Slot(result=bool)
    def is_task_running(self):
        return self.wait_flag

    @Slot(bool)
    def show_cropping_tool(self, allow_cropping):
        self.showCroppingToolSignal.emit(allow_cropping)

    @Slot(bool)
    def perform_cropping(self, allowed):
        self.performCroppingSignal.emit(allowed)

    @Slot( int, int, int, int, int, int)
    def crop_image(self, x, y, crop_width, crop_height, qimg_width, qimg_height):
        """Crop image using PIL and save it."""
        try:
            sgt_obj = self.get_selected_sgt_obj()
            sgt_obj.ntwk_p.crop_image(x, y, crop_width, crop_height, qimg_width, qimg_height)

            # Emit signal to update UI with new image
            self.changeImageSignal.emit()
            self.showCroppingToolSignal.emit(False)
            self.showUnCroppingToolSignal.emit(True)
        except Exception as err:
            logging.exception("Cropping Error: %s", err, extra={'user': 'SGT Logs'})
            self.showAlertSignal.emit("Cropping Error", "Error occurred while cropping image. Close the app and try again.")

    @Slot(bool)
    def undo_cropping(self, undo: bool = True):
        if undo:
            sgt_obj = self.get_selected_sgt_obj()
            sgt_obj.ntwk_p.undo_cropping()

            # Emit signal to update UI with new image
            self.changeImageSignal.emit()
            self.showUnCroppingToolSignal.emit(False)

    @Slot(bool)
    def enable_rectangular_selection(self, enabled):
        self.enableRectangularSelectionSignal.emit(enabled)

    @Slot(result=bool)
    def enable_prev_nav_btn(self):
        if (self.selected_sgt_obj_index == 0) or self.is_task_running():
            return False
        else:
            return True

    @Slot(result=bool)
    def enable_next_nav_btn(self):
        if (self.selected_sgt_obj_index == (len(self.sgt_objs) - 1)) or self.is_task_running():
            return False
        else:
            return True

    @Slot(str, result=bool)
    def add_single_image(self, image_path):
        """Verify and validate an image path, use it to create an SGT object and load it in view."""
        is_created = self.create_sgt_object(image_path)
        if is_created:
            # pos = (len(self.sgt_objs) - 1)
            self.load_image(reload_thumbnails=True)
            return True
        return False

    @Slot(str, result=bool)
    def add_multiple_images(self, img_dir_path):
        """
        Verify and validate multiple image paths, use each to create an SGT object, then load the last one in view.
        """

        success, result = verify_path(img_dir_path)
        if success:
            img_dir_path = result
        else:
            logging.info(result, extra={'user': 'SGT Logs'})
            self.showAlertSignal.emit("File/Directory Error", result)
            return False

        files = os.listdir(img_dir_path)
        files = sorted(files)
        for a_file in files:
            allowed_extensions = tuple(ext[1:] if ext.startswith('*.') else ext for ext in ALLOWED_IMG_EXTENSIONS)
            if a_file.endswith(allowed_extensions):
                img_path = os.path.join(str(img_dir_path), a_file)
                _ = self.create_sgt_object(img_path)

        if len(self.sgt_objs) <= 0:
            logging.info("File Error: Files have to be either .tif .png .jpg .jpeg", extra={'user': 'SGT Logs'})
            self.showAlertSignal.emit("File Error", "No workable images found! Files have to be either .tif, .png, .jpg or .jpeg")
            return False
        else:
            # pos = (len(self.sgt_objs) - 1)
            self.load_image(reload_thumbnails=True)
            return True

    @Slot(str, str, result=bool)
    def create_sgt_project(self, proj_name, dir_path):
        """Creates a '.sgtproj' inside the selected directory"""

        self.project_open = False
        success, result = verify_path(dir_path)
        if success:
            dir_path = result
        else:
            logging.info(result, extra={'user': 'SGT Logs'})
            self.showAlertSignal.emit("File/Directory Error", result)
            return False

        proj_name += '.sgtproj'
        proj_path = os.path.join(str(dir_path), proj_name)

        try:
            if os.path.exists(proj_path):
                logging.info(f"Project '{proj_name}' already exists.", extra={'user': 'SGT Logs'})
                self.showAlertSignal.emit("Project Error", f"Error: Project '{proj_name}' already exists.")
                return False

            # Open the file in the 'write' mode ('w').
            # This will create the file if it doesn't exist
            with open(proj_path, 'w'):
                pass  # Do nothing, just create the file (updates will be done automatically/dynamically)

            # Update and notify QML
            self.project_data["name"] = proj_name
            self.project_data["file_path"] = proj_path
            self.project_open = True
            self.projectOpenedSignal.emit(proj_name)
            logging.info(f"File '{proj_name}' created successfully in '{dir_path}'.", extra={'user': 'SGT Logs'})
            return True
        except Exception as err:
            logging.exception("Create Project Error: %s", err, extra={'user': 'SGT Logs'})
            self.showAlertSignal.emit("Create Project Error", "Failed to create SGT project. Close the app and try again.")
            return False

    @Slot(str, result=bool)
    def open_sgt_project(self, sgt_path):
        """Opens and loads the SGT project from the '.sgtproj' file"""
        if self.wait_flag:
            logging.info("Please Wait: Another Task Running!", extra={'user': 'SGT Logs'})
            self.showAlertSignal.emit("Please Wait", "Another Task Running!")
            return False

        try:
            self.wait_flag = True
            self.project_open = False
            # Verify the path
            success, result = verify_path(sgt_path)
            if success:
                sgt_path = result
            else:
                logging.info(result, extra={'user': 'SGT Logs'})
                self.showAlertSignal.emit("File/Directory Error", result)
                self.wait_flag = False
                return False
            img_dir, proj_name = os.path.split(str(sgt_path))

            # Read and load project data and SGT objects
            with open(str(sgt_path), 'rb') as sgt_file:
                self.sgt_objs = pickle.load(sgt_file)

            if self.sgt_objs:
                key_list = list(self.sgt_objs.keys())
                for key in key_list:
                    self.sgt_objs[key].ntwk_p.output_dir = img_dir

            # Update and notify QML
            self.project_data["name"] = proj_name
            self.project_data["file_path"] = str(sgt_path)
            self.wait_flag = False
            self.project_open = True
            self.projectOpenedSignal.emit(proj_name)

            # Load Image to GUI - activates QML
            self.load_image(reload_thumbnails=True)
            logging.info(f"File '{proj_name}' opened successfully in '{sgt_path}'.", extra={'user': 'SGT Logs'})
            return True
        except Exception as err:
            self.wait_flag = False
            logging.exception("Project Opening Error: %s", err, extra={'user': 'SGT Logs'})
            self.showAlertSignal.emit("Open Project Error", "Unable to open .sgtproj file! Try again. If the "
                                                            "issue persists, the file may be corrupted or incompatible. "
                                                            "Consider restoring from a backup or contacting support for "
                                                            "assistance.")
            return False
