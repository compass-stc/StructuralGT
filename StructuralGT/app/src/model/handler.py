"""Thread-safe Handler for metadata and network objects."""

import threading
import pandas as pd
from typing import Optional, Any, Dict
import pathlib
from StructuralGT.networks import Network, PointNetwork


class ThreadSafeDict:
    """Thread-safe dictionary."""

    def __init__(self):
        """Initialize the thread-safe dictionary."""
        self._dict: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def __getitem__(self, key: str) -> Any:
        """Get the value for the given key."""
        with self._lock:
            return self._dict.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set the value for the given key."""
        with self._lock:
            self._dict[key] = value

    def __copy__(self) -> "ThreadSafeDict":
        """Copy the thread-safe dictionary."""
        with self._lock:
            return ThreadSafeDict(**self._dict)


class Handler(ThreadSafeDict):
    """Handler for metadata and network objects."""

    def __init__(self, input_dir: str):
        """Initialize the base handler."""
        super().__init__()
        self["paths"] = {"input_dir": input_dir}
        self["ui_properties"] = {
            # "Raw Image", "Binarized Image", "Extracted Graph"
            "display_type": "Raw Image",
            "selected_slice_index": 0,
            "raw_loaded": False,
            "binarized_loaded": False,
            "extracted_loaded": False,
        }
        self["network_properties"] = {
            "dim": None,  # 2 or 3
            "diameter": None,
            "density": None,
            "average_clustering_coefficient": None,
            "assortativity": None,
            "average_closeness": None,
            "average_degree": None,
            "nematic_order_parameter": None,
            "effective_resistance": None,
        }
        self["tasks"] = {
            "Binarize": None,
            "Extract Graph": None,
            "Compute Graph Properties": None,
        }


class NetworkHandler(Handler):
    """Handler for network objects."""

    def __init__(self, input_dir: str, dim: int = 2):
        """Initialize the network handler."""
        super().__init__(input_dir)
        self["network"] = Network(directory=input_dir, dim=dim)
        self["ui_properties"]["dim"] = dim
        self["ui_properties"]["image_shape"] = self["network"].image.shape
        self["binarize_options"] = {
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
    """Handler for point network objects."""

    def __init__(self, input_dir: str, cutoff: float = 1200.0):
        """Initialize the point network handler."""
        super().__init__(input_dir)
        positions = pd.read_csv(self["paths"]["input_dir"])
        positions = positions[["x", "y", "z"]].values
        self["network"] = PointNetwork(positions, cutoff)
        self["network"].point_to_skel(
            filename=str(
                pathlib.Path(self["paths"]["input_dir"]).parent / "skel.gsd"
            )
        )
        self["ui_properties"]["cutoff"] = cutoff
        self["ui_properties"]["dim"] = 3
        self["ui_properties"]["extracted_loaded"] = True


class HandlerRegistry:
    """Thread-safe registry for Network/PointNetwork Handlers."""

    def __init__(self):
        """Initialize the handler registry."""
        self._handlers_lock = threading.Lock()
        self._handlers: list[Optional[Handler]] = []
        self._selected_index: int = -1  # -1 means no selection

    def add(self, handler: Handler) -> bool:
        """Add a handler to the registry."""
        with self._handlers_lock:
            index = len(self._handlers)
            self._handlers.append(handler)
            self._selected_index = index
            return True

    def get(self, index: int) -> Optional[Handler]:
        """Get the handler at the given index."""
        with self._handlers_lock:
            if not (0 <= index < len(self._handlers)):
                return None
            return self._handlers[index]

    def get_all(self) -> list[Handler]:
        """Get all handlers."""
        with self._handlers_lock:
            return [h for h in self._handlers if h is not None]

    def select(self, index: int) -> bool:
        """Select the handler at the given index."""
        with self._handlers_lock:
            if not (0 <= index < len(self._handlers)):
                return False
            if self._handlers[index] is None:
                return False
            self._selected_index = index
            return True

    def get_selected(self) -> Optional[Handler]:
        """Get the currently selected handler."""
        return self.get(self._selected_index)

    def get_selected_index(self) -> int:
        """Get the index of the currently selected handler."""
        with self._handlers_lock:
            return self._selected_index

    def delete(self, index: int) -> bool:
        """Delete the handler at the given index."""
        with self._handlers_lock:
            if not (0 <= index < len(self._handlers)):
                return False
            self._handlers[index] = None
            if index == self._selected_index:
                self._selected_index = -1
                for i in range(len(self._handlers)):
                    if self._handlers[i] is not None:
                        self._selected_index = i
                        break
            return True

    def delete_all(self) -> bool:
        """Delete all handlers."""
        with self._handlers_lock:
            self._handlers = []
            self._selected_index = -1
            return True

    def count(self) -> int:
        """Get the number of handlers."""
        with self._handlers_lock:
            return sum(1 for handler in self._handlers if handler is not None)

    def get_valid_indices(self) -> list[int]:
        """Get list of valid handler indices."""
        with self._handlers_lock:
            return [
                i
                for i, handler in enumerate(self._handlers)
                if handler is not None
            ]

    def task_count(self) -> int:
        """Get the number of tasks."""
        with self._handlers_lock:
            count = 0
            for handler in self._handlers:
                if handler is not None:
                    tasks = handler["tasks"]
                    count += sum(
                        1 for task in tasks.values() if task is not None
                    )
            return count
