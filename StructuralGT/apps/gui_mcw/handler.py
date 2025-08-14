"""Network objects handler for StructuralGT GUI."""


import pathlib
from enum import Enum
from typing import Optional, Union

import pandas as pd

from StructuralGT.networks import Network, PointNetwork


class Handler:
    """Base class to handle different types of networks."""

    def __init__(self, input_dir: str, temp_dir: str):
        self.input_dir = input_dir
        self.temp_dir = temp_dir # TODO: store the results in a temporary directory?
        self.network = None # Network or PointNetwork
        self.dim = None # 2D or 3D
        self.properties = {
            "Diameter": None,
            "Density": None,
            "Average Clustering Coefficient": None,
            "Assortativity": None,
            "Average Closeness": None,
            "Average Degree": None,
            "Nematic Order Parameter": None,
            "Effective Resistance": None
        }

class NetworkHandler(Handler):
    """Class to handle Network loading and processing."""

    def __init__(self, input_dir: str, temp_dir: str, dim: int):
        super().__init__(input_dir, temp_dir)
        self.dim = dim
        self.network = Network(directory=input_dir, dim=dim)
        self.img_loaded = False
        self.binary_loaded = False
        self.graph_loaded = False
        self.display_type = "raw" # "raw", "binarized", "extracted"
        self.selected_slice_index = 0
        self.options = {
            "Thresh_method": 0,
            "gamma": 1.001,
            "md_filter": 0,
            "g_blur": 0,
            "autolvl": 0,
            "fg_color": 0,
            "laplacian": 0,
            "scharr": 0,
            "sobel": 0,
            "lowpass": 0,
            "asize": 3,
            "bsize": 1,
            "wsize": 1,
            "thresh": 128.0,
        }

class PointNetworkHandler(Handler):
    """Class to handle PointNetwork loading and processing."""

    def __init__(self, input_dir: str, temp_dir: str, cutoff: float):
        super().__init__(input_dir, temp_dir)
        positions = pd.read_csv(self.input_dir)
        positions = positions[["x", "y", "z"]].values
        self.network = PointNetwork(positions, cutoff)
        self.network.point_to_skel(
            filename=str(pathlib.Path(self.input_dir).parent / "skel.gsd")
        )

HandlerType = Union[NetworkHandler, PointNetworkHandler]

class HandlerRegistry:
    """Registry record for all network handlers."""

    def __init__(self):
        self._handlers: list[HandlerType] = []
        self._selected_index: int = -1 # -1 means no selection

    def add(self, handler: HandlerType) -> int:
        """Add a network handler to the registry."""
        self._handlers.append(handler)
        if self._selected_index == -1:
            self._selected_index = 0
        return len(self._handlers) - 1

    def delete(self, index: int) -> bool:
        """Delete a network handler from the registry."""
        if 0 <= index < len(self._handlers):
            del self._handlers[index]
            if not self._handlers:
                self._selected_index = -1
            elif self._selected_index >= index:
                self._selected_index = max(0, self._selected_index - 1)
            return True
        return False

    def delete_all(self):
        """Delete all network handlers from the registry."""
        self._handlers.clear()
        self._selected_index = -1

    def get(self, index: int) -> Optional[HandlerType]:
        """Get a network handler by index."""
        if 0 <= index < len(self._handlers):
            return self._handlers[index]
        return None

    def get_selected(self) -> Optional[HandlerType]:
        """Get the currently selected network handler."""
        if self._selected_index == -1:
            return None
        return self._handlers[self._selected_index]

    def get_all(self) -> list[HandlerType]:
        """List all network handlers."""
        return self._handlers

    def select(self, index: int) -> bool:
        """Select a network handler by index."""
        if 0 <= index < len(self._handlers):
            self._selected_index = index
            return True
        return False

    def get_selected_index(self) -> int:
        """Get the index of the currently selected network handler."""
        return self._selected_index

    def count(self) -> int:
        """Get the number of network handlers in the registry."""
        return len(self._handlers)

    def list_for_ui(self) -> list[dict]:
        """Return data for ListModel."""
        return [
            {
                "id": i,
                "name": pathlib.Path(handler.input_dir).name,
            }
            for i, handler in enumerate(self._handlers)
        ]
