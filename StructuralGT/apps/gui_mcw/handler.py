from StructuralGT.networks import Network, PointNetwork
import pandas as pd
import pathlib

class Handler:
    """Base class to handle different types of networks."""

    def __init__(self, input_dir: str, temp_dir: str):
        self.input_dir = input_dir
        self.temp_dir = temp_dir
        self.network = None
        self.display_type = None
        self.dim = None
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
        self.display_type = "original"
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
        # TODO: Change to pathlib
        self.network.point_to_skel(filename=os.path.join(os.path.dirname(self.input_dir), "skel.gsd"))
