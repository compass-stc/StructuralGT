import json
import logging
import pathlib
import pickle
import shutil
import sys
import tempfile
from typing import Optional

from ..utils.handler import HandlerRegistry, NetworkHandler, PointNetworkHandler

ALLOWED_IMG_EXTENSIONS = ["*.jpg", "*.jpeg", "*.tif", "*.tiff"]
ALLOWED_CSV_EXTENSIONS = ["*.csv"]
ALLOWED_EXPORT_EXTENSIONS = ["*.json", "*.csv", "*.png"]


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
        if option == "export":
            pattern = " ".join(ALLOWED_EXPORT_EXTENSIONS)
            return f"Export files ({pattern})"
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

    def create_network_handler(self, path: str, dim: int) -> NetworkHandler | None:
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

    def save_sgt_project(self, project_path: str) -> bool:
        """Save the current HandlerRegistry to a .sgtproj file."""
        try:
            project_path = self.verify_path(project_path)
            project_file = pathlib.Path(project_path)

            # Ensure the directory exists
            project_file.parent.mkdir(parents=True, exist_ok=True)

            # Create project data structure with direct handler objects
            project_data = {
                "handlers": self._registry.get_all(),  # Direct handler objects
                "selected_index": self._registry.get_selected_index(),
            }

            # Save to pickle file
            with open(project_file, "wb") as f:
                pickle.dump(project_data, f)

            logging.info(f"Project saved to: {project_file}")
            return True

        except Exception as e:
            logging.error(f"Error saving project: {e}")
            return False

    def open_sgt_project(self, project_path: str) -> bool:
        """Load a HandlerRegistry from a .sgtproj file."""
        try:
            project_path = self.verify_path(project_path)
            project_file = pathlib.Path(project_path)

            if not project_file.exists():
                logging.error(f"Project file not found: {project_file}")
                return False

            # Load project data
            with open(project_file, "rb") as f:
                project_data = pickle.load(f)

            # Clear current registry
            self._registry.delete_all()

            # Restore handlers directly from saved objects
            handlers = project_data.get("handlers", [])
            for handler in handlers:
                self._registry.add(handler)

            # Restore selected index
            selected_index = project_data.get("selected_index", -1)
            if 0 <= selected_index < self._registry.count():
                self._registry.select(selected_index)

            logging.info(f"Project loaded from: {project_file}")
            return True

        except Exception as e:
            logging.error(f"Error loading project: {e}")
            return False

    def close_sgt_project(self) -> bool:
        """Close the currently opened SGT project."""
        try:
            self._registry.delete_all()
            logging.info("Project closed")
            return True
        except Exception as e:
            logging.error(f"Error closing project: {e}")
            return False

    def rename_sgt_project(self, old_path: str, new_path: str) -> bool:
        """Rename an SGT project file."""
        try:
            old_path = self.verify_path(old_path)
            new_path = self.verify_path(new_path)

            old_file = pathlib.Path(old_path)
            new_file = pathlib.Path(new_path)

            if not old_file.exists():
                logging.error(f"Project file not found: {old_file}")
                return False

            # Rename the file
            old_file.rename(new_file)

            logging.info(f"Project renamed from {old_file} to {new_file}")
            return True

        except Exception as e:
            logging.error(f"Error renaming project: {e}")
            return False

    def export_binarize_options(
        self, index: int, export_dir: str, filename: str
    ) -> bool:
        """Export the binarization options for the selected NetworkHandler."""
        try:
            handler = self._registry.get(index)
            if not handler:
                logging.error(f"Handler with index {index} not found.")
                return False

            if isinstance(handler, PointNetworkHandler):
                logging.warning(
                    "Binarization options not applicable for PointNetworkHandler."
                )
                return False

            if not hasattr(handler, "options") or not handler.options:
                logging.warning("No binarization options available for export.")
                return False

            export_dir = self.verify_path(export_dir)
            export_path = pathlib.Path(export_dir)
            export_path.mkdir(parents=True, exist_ok=True)

            # Save as JSON file
            json_path = export_path / f"{filename}.json"
            with open(json_path, "w") as f:
                json.dump(handler.options, f, indent=2)

            logging.info(f"Exported binarization options to: {json_path}")
            return True

        except Exception as e:
            logging.error(f"Error exporting binarization options: {e}")
            return False

    def export_extracted_graph(
        self, index: int, export_dir: str, filename: str
    ) -> bool:
        """Export the extracted graph as image for the selected NetworkHandler."""
        try:
            handler = self._registry.get(index)
            if not handler:
                logging.error(f"Handler with index {index} not found.")
                return False

            if not (hasattr(handler, "graph_loaded") and handler.graph_loaded):
                logging.warning("No extracted graph available for export.")
                return False

            export_dir = self.verify_path(export_dir)
            export_path = pathlib.Path(export_dir)
            export_path.mkdir(parents=True, exist_ok=True)

            # Get the extracted graph image from the handler
            if hasattr(handler, "network") and hasattr(handler.network, "graph"):
                # For 2D networks, we can get the extracted graph image
                if handler.dim == 2 and hasattr(handler, "network"):
                    try:
                        import numpy as np
                        from PIL import Image
                        from matplotlib.backends.backend_agg import FigureCanvasAgg

                        # Get the extracted graph image using the same method as image provider
                        ax = handler.network.graph_plot()
                        fig = ax.get_figure()
                        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

                        canvas = FigureCanvasAgg(fig)
                        canvas.draw()

                        width, height = canvas.get_width_height()
                        buf = canvas.buffer_rgba()
                        image = np.asarray(buf, dtype=np.uint8).reshape(
                            (height, width, 4)
                        )

                        # Convert RGBA to RGB
                        if image.shape[2] == 4:
                            image = image[:, :, :3]

                        # Save as image
                        image_path = export_path / f"{filename}.png"
                        Image.fromarray(image).save(image_path)

                        # Close the figure to free memory
                        import matplotlib.pyplot as plt

                        plt.close(fig)

                        logging.info(f"Exported extracted graph image to: {image_path}")
                        return True
                    except Exception as e:
                        logging.error(f"Error creating graph image: {e}")
                        return False
                else:
                    logging.warning(
                        "Graph image export only supported for 2D networks."
                    )
                    return False
            else:
                logging.warning("No graph available for image export.")
                return False

        except Exception as e:
            logging.error(f"Error exporting extracted graph: {e}")
            return False

    def export_graph_properties(
        self, index: int, export_dir: str, filename: str
    ) -> bool:
        """Export the graph properties for the selected NetworkHandler."""
        try:
            handler = self._registry.get(index)
            if not handler:
                logging.error(f"Handler with index {index} not found.")
                return False

            if not hasattr(handler, "properties") or not handler.properties:
                logging.warning("No graph properties available for export.")
                return False

            export_dir = self.verify_path(export_dir)
            export_path = pathlib.Path(export_dir)
            export_path.mkdir(parents=True, exist_ok=True)

            # Prepare data for CSV export
            properties_data = []
            for key, value in handler.properties.items():
                if value is not None and value != "":
                    properties_data.append([key, str(value)])

            # Add basic graph info if available
            if hasattr(handler, "network") and hasattr(handler.network, "graph"):
                properties_data.insert(
                    0, ["Edge Count", str(handler.network.graph.ecount())]
                )
                properties_data.insert(
                    1, ["Node Count", str(handler.network.graph.vcount())]
                )

            # Write CSV file
            csv_path = export_path / f"{filename}.csv"
            with open(csv_path, "w") as f:
                f.write("Property,Value\n")
                for prop, val in properties_data:
                    f.write(f"{prop},{val}\n")

            logging.info(f"Exported graph properties to: {csv_path}")
            return True

        except Exception as e:
            logging.error(f"Error exporting graph properties: {e}")
            return False
