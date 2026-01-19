"""UI service for StructuralGT GUI."""

import cv2
import pathlib
import numpy as np
from pathlib import Path
import qdarktheme
from typing import Optional
from model.handler import HandlerRegistry, NetworkHandler, PointNetworkHandler


class UIService:
    """UI service for StructuralGT GUI."""

    @staticmethod
    def set_selected_index(handler_registry: HandlerRegistry, index: int):
        """Select the handler at the given index."""
        handler_registry.select(index)
        return

    @staticmethod
    def set_selected_slice_index(handler_registry: HandlerRegistry, index: int):
        """Set the selected handler at the given slice index."""
        handler = handler_registry.get_selected()
        if handler and isinstance(handler, NetworkHandler):
            handler["ui_properties"]["selected_slice_index"] = index
        return

    @staticmethod
    def get_selected_slice_raw_image(
        handler_registry: HandlerRegistry, index: int
    ) -> Optional[np.ndarray]:
        """Get the selected slice raw image from the selected handler."""
        handler = handler_registry.get_selected()
        image = None
        if handler and isinstance(handler, NetworkHandler):
            dim = handler["ui_properties"]["dim"]
            if dim == 2:
                image = handler["network"].image
            elif dim == 3:
                image = handler["network"].image[index, :, :]
        return image

    @staticmethod
    def get_selected_slice_binarized_image(
        handler_registry: HandlerRegistry, index: int
    ) -> Optional[np.ndarray]:
        """Get the selected slice binarized image from the selected handler."""
        handler = handler_registry.get_selected()
        image = None
        if handler and isinstance(handler, NetworkHandler):
            input_dir = handler["paths"]["input_dir"]
            dim = handler["ui_properties"]["dim"]
            index = (
                index + 1 if dim == 3 else index
            )  # FIXME: This is restricted by StructuralGT library
            binarized_filename = f"slice{str(index).zfill(4)}.tiff"
            image_path = pathlib.Path(input_dir) / "Binarized" / binarized_filename
            image = cv2.imread(str(image_path))
        return image

    @staticmethod
    def get_selected_extracted_graph(
        handler_registry: HandlerRegistry,
    ) -> Optional[str]:
        """Get the selected extracted graph from the selected handler."""
        handler = handler_registry.get_selected()
        gsd_file = None
        if handler:
            input_dir = handler["paths"]["input_dir"]
            if isinstance(handler, NetworkHandler):
                gsd_file = pathlib.Path(input_dir) / "Binarized" / "network.gsd"
            elif isinstance(handler, PointNetworkHandler):
                gsd_file = pathlib.Path(input_dir).parent / "skel.gsd"
        return str(gsd_file)

    @staticmethod
    def load_theme(theme: str, custom_styles: str) -> str:
        """Load theme stylesheet with custom styles."""
        base_stylesheet = qdarktheme.load_stylesheet(theme=theme)
        combined = base_stylesheet + "\n" + UIService.get_custom_styles()
        return combined

    @staticmethod
    def get_custom_styles() -> str:
        """Get the custom styles from file system."""
        import sys

        # PyInstaller environment
        if hasattr(sys, "_MEIPASS"):
            base_path = pathlib.Path(sys._MEIPASS)
            style_file = (
                base_path / "app" / "view" / "resources" / "style" / "custom_styles.qss"
            )
        # Normal environment
        else:
            style_file = (
                pathlib.Path(__file__).parent.parent
                / "view"
                / "resources"
                / "style"
                / "custom_styles.qss"
            )

        if style_file.exists():
            content = style_file.read_text(encoding="utf-8")
            return content
        else:
            return ""
