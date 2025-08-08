import os
from StructuralGT.networks import PointNetwork


class CSVHandler:
    """Class to handle CSV point cloud data."""

    def __init__(self, csv_path, point_network):
        self.csv_path = csv_path
        self.point_network = point_network
        self.is_3d = point_network.dim == 3
        self.img_loaded = True  # CSV data is immediately available
        self.binary_loaded = False  # Not applicable for point networks
        self.graph_loaded = False
        self.display_type = "original"
        self.selected_slice_index = 0
        
        # Create skeleton/graph file for visualization
        temp_dir = os.path.dirname(csv_path)
        skel_filename = os.path.join(temp_dir, "point_network.gsd")
        self.point_network.point_to_skel(skel_filename)
        
        self.options = {}  # CSV doesn't need binarization options
        
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
    
    @property
    def img_path(self):
        """Return a path-like object for compatibility with ImageHandler interface."""
        class PathLike:
            def __init__(self, path):
                self.name = os.path.basename(path)
        return PathLike(self.csv_path)
    
    @property
    def network(self):
        """Return the point network for compatibility with ImageHandler interface."""
        return self.point_network
