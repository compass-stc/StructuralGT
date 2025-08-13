import sys
import pathlib
import logging
import tempfile
import shutil
from PySide6.QtGui import QIcon
from PySide6.QtCore import QObject, Signal, Slot, QDir
from PySide6.QtWidgets import QApplication, QTreeView, QFileSystemModel 

from .handler import NetworkHandler, PointNetworkHandler


ALLOWED_IMG_EXTENSIONS = ["*.jpg", "*.jpeg", "*.tif", "*.tiff"]
ALLOWED_CSV_EXTENSIONS = ["*.csv"]


class FileController(QObject):

    projectOpened = Signal()
    projectClosed = Signal()
    projectChanged = Signal()
    selectedIndexChanged = Signal(int)
    showAlert = Signal(str, str)

    def __init__(self, qml_app: QApplication):
        super().__init__()
        self.qml_app = qml_app
        self.handlers = []
        self.selected_index = 0
        self.project_opened = False
        self.project_temp_dir = tempfile.mkdtemp(prefix="sgt_proj_")

    @Slot(str, result=str)
    def get_file_extensions(self, option: str) -> str:
        if option == "img":
            pattern = " ".join(ALLOWED_IMG_EXTENSIONS)
            return f"Image files ({pattern})"
        elif option == "proj":
            return "Project files (*.sgtproj)"
        elif option == "csv":
            pattern = " ".join(ALLOWED_CSV_EXTENSIONS)
            return f"CSV files ({pattern})"
        else:
            return ""

    def verify_path(self, path: str) -> str:
        if not path:
            raise ValueError("Path cannot be empty.")

        # Convert QML "file:///" path format to a proper OS path
        if path.startswith("file:///"):
            if sys.platform.startswith("win"):
                # Windows (remove extra '/')
                path = path[8:]
            else:
                # MacOS/Linux (remove "file://")
                path = path[7:]

        # Normalize the path
        return str(pathlib.Path(path).resolve())

    def get_selected_handler(self) -> NetworkHandler | PointNetworkHandler | None:
        try:
            return self.handlers[self.selected_index]
        except IndexError:
            logging.error(
                "No handler found at index %d", self.selected_index
            )
            self.showAlert.emit(
                "Network Error", "No network added! Please import/add a network."
            )
            return None

    @Slot(str, int, result=bool)
    def add_network_handler(self, path: str, dim: int) -> bool:
        try:
            path = self.verify_path(path)
            if not path:
                return False
            logging.info(f"Creating {dim}D NetworkHandler for path: {path}")

            # TODO: Create temp_dir for output
            temp_dir = tempfile.mkdtemp(dir=self.project_temp_dir)
            self.handlers.append(NetworkHandler(path, temp_dir, dim))
            # TODO: update the front end
            return True
        except Exception as e:
            logging.error(f"Error creating NetworkHandler: {e}")
            self.showAlert.emit("Network Error", "Error creating network.")
            return False

    @Slot(str, float, result=bool)
    def add_point_network_handler(self, path: str, cutoff: float) -> bool:
        try:
            path = self.verify_path(path)
            if not path:
                return False
            logging.info(f"Creating PointNetworkHandler for path: {path} with cutoff: {cutoff}")

            # TODO: Create temp_dir for output
            temp_dir = tempfile.mkdtemp(dir=self.project_temp_dir)
            self.handlers.append(PointNetworkHandler(path, temp_dir, cutoff))
            # TODO: update the front end
            return True
        except Exception as e:
            logging.error(f"Error creating PointNetworkHandler: {e}")
            self.showAlert.emit("Network Error", "Error creating point network.")
            return False

    @Slot(int, result=bool)
    def delete_handler(self, index: int) -> bool:
        # TODO: this may be implemented later
        pass

    @Slot(str, str, result=bool)
    def create_sgt_project(self, proj_name: str, project_path: str) -> bool:
        # project_path is the directory for the project
        pass

    @Slot(str, result=bool)
    def open_sgt_project(self, proj_path: str) -> bool:
        pass

    @Slot(result=bool)
    def close_sgt_project(self) -> bool:
        pass

    @Slot(result=bool)
    def save_sgt_project(self) -> bool:
        pass

    @Slot(str, result=bool)
    def rename_sgt_project(self, new_name: str) -> bool:
        pass

    @Slot(str, result=bool)
    def set_output_dir(self, dir_path: str) -> bool:
        pass
