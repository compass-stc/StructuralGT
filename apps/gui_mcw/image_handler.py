from StructuralGT.networks import Network


class ImageHandler:
    """Class to handle image loading and processing."""

    def __init__(self, img_path, is_3d=False):
        self.img_path = img_path
        self.is_3d = is_3d

        if is_3d:
            self.network = Network(img_path, dim=3)
        else:
            self.network = Network(img_path.name)

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
