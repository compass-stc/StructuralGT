import logging
import pathlib
import shutil
import sys
import tempfile
from typing import Optional

from ..utils.handler import HandlerRegistry, NetworkHandler, PointNetworkHandler

ALLOWED_IMG_EXTENSIONS = ["*.jpg", "*.jpeg", "*.tif", "*.tiff"]
ALLOWED_CSV_EXTENSIONS = ["*.csv"]


class FileController:
    """Class to manage file operations for the GUI."""

    def __init__(self, registry: HandlerRegistry, project_root: Optional[str] = None):
        super().__init__()
        self._registry = registry
        if project_root:
            self._project_root = pathlib.Path(project_root)
        else:
            self._temp_dir = tempfile.TemporaryDirectory(prefix="sgt_proj_")
            self._project_root = pathlib.Path(self._temp_dir.name)

    @staticmethod
    def file_filters(option: str) -> str:
        """Return file filters based on the option."""
        if option == "img":
            pattern = " ".join(ALLOWED_IMG_EXTENSIONS)
            return f"Image files ({pattern})"
        if option == "proj":
            return "Project files (*.sgtproj)"
        if option == "csv":
            pattern = " ".join(ALLOWED_CSV_EXTENSIONS)
            return f"CSV files ({pattern})"
        return ""

    @staticmethod
    def verify_path(path: str) -> str:
        """Verify and normalize the file path."""
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

    def create_network_handler(
            self, path: str, dim: int
        ) -> NetworkHandler | None:
        """Create a NetworkHandler for the given path and dimension."""
        try:
            path = self.verify_path(path)
            if not path:
                return None
            logging.info(f"Creating {dim}D NetworkHandler for path: {path}")
            temp_dir = tempfile.mkdtemp(dir=self._project_root)
            return NetworkHandler(path, temp_dir, dim)
        except Exception as e:
            logging.error(f"Error creating NetworkHandler: {e}")
            return None

    def create_point_network_handler(
            self, path: str, cutoff: float
        ) -> PointNetworkHandler | None:
        """Create a PointNetworkHandler for the given path and cutoff."""
        try:
            path = self.verify_path(path)
            if not path:
                return None
            logging.info(
                f"Creating PointNetworkHandler for path: {path} with cutoff: {cutoff}"
            )

            temp_dir = tempfile.mkdtemp(dir=self._project_root)
            return PointNetworkHandler(path, temp_dir, cutoff)
        except Exception as e:
            logging.error(f"Error creating PointNetworkHandler: {e}")
            return None

    def set_project_root(self, project_root: str) -> None:
        """Set the project root directory."""
        self._project_root = project_root

    def open_sgt_project(self, project_path: str) -> bool:
        """Open an existing SGT project."""
        return True

    def close_sgt_project(self) -> bool:
        """Close the currently opened SGT project."""
        return True

    def save_sgt_project(self) -> bool:
        """Save the currently opened SGT project."""
        return True

    def rename_sgt_project(self, new_name: str) -> bool:
        """Rename the currently opened SGT project."""
        return True
