from StructuralGT.networks import Network


class ImageHandler:
    """Class to handle image loading and processing."""

    def __init__(self, img_path, is_3d=False):
        self._img_path = img_path
        self._is_3d = is_3d
        if is_3d:
            self._network = Network(img_path, dim=3)
        else:
            self._network = Network(img_path.name)

        self._img_loaded = False
        self._display_type = "original"
        self._binary_loaded = False
        self._graph_loaded = False

        self._selected_slice_index = 0

    @property
    def img_path(self):
        return self._img_path

    @property
    def is_3d(self):
        return self._is_3d

    @property
    def network(self):
        return self._network

    @property
    def img_loaded(self):
        return self._img_loaded

    @img_loaded.setter
    def img_loaded(self, value):
        self._img_loaded = value

    @property
    def display_type(self):
        return self._display_type

    @display_type.setter
    def display_type(self, value):
        self._display_type = value

    @property
    def binary_loaded(self):
        return self._binary_loaded

    @binary_loaded.setter
    def binary_loaded(self, value):
        self._binary_loaded = value

    @property
    def graph_loaded(self):
        return self._graph_loaded

    @graph_loaded.setter
    def graph_loaded(self, value):
        self._graph_loaded = value

    @property
    def selected_slice_index(self):
        return self._selected_slice_index

    @selected_slice_index.setter
    def selected_slice_index(self, value):
        self._selected_slice_index = value
