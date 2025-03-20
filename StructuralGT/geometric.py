# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import warnings

import freud
import numpy as np

from StructuralGT.util import _Compute


def largest_rotating_crop(image_shape):
    """Returns the crop coordinates for the largest square that would remain
    inside during any rotation of the image. Supports 2D images only.

    Args:
        image_shape (tuple): The dimensions of the image to be cropped.

    Returns:
        (list): The coordinates of the crop in the format [L1,L2,L3,L4], where
        L1 and L2 are the lower and upper x-coordinates of the crop, and L3 and
        L4 are the lower and upper y-coordinates of the crop.
    """

    short_length = image_shape[image_shape == max(image_shape)]
    long_length = max(image_shape)
    rotated_diagonal_length = (short_length**2 / 2) ** 0.5

    L1 = int((short_length - rotated_diagonal_length) / 2)
    L2 = int(rotated_diagonal_length + L1)
    L3 = int((long_length - rotated_diagonal_length) / 2)
    L4 = int(rotated_diagonal_length + L3)

    return [L1, L2, L3, L4]


def vector_to_angle(vector):
    """Converts 2D orientation vector to angle that the vector makes with
    the x-axis, in degrees. Function range is 0 to 180 degrees.

    Args:
        vector (tuple): Orientation of a 2D edge

    Returns:
        angle (float): Angle that vector makes with the x-axis (i.e. 0th
        dimension of the vector).
    """

    del_x, del_y = vector[1], vector[0]
    if del_x == 0 and del_y == 0:
        warnings.warn("Zero vector encountered. Returning 0")
        return 0
    if del_x == 0:
        return 90
    if del_y == 0:
        return 0
    if del_x * del_y > 0:
        return float(np.arctan(del_y / del_x) * 180 / np.pi)
    if del_x * del_y < 0:
        return float(np.arctan(del_y / del_x) * 180 / np.pi + 180)


class Nematic(_Compute):
    """Computes the nematic tensor of the graph. For details on how it
    quantifies orientational anisotropy, see :cite:`Mottram2014`. If the edge
    occupies a single voxel (and therefore has a zero vector orientation),
    it is not used in calculating the nematic tensor. However it is still
    returned as past of the orientations array so that the length of the
    orientations array is equal to the edge count."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compute(self, network):
        """Computes the nematic tensor of the graph."""

        _orientations = np.zeros((network.graph.ecount(), network.dim))
        for i, edge in enumerate(network.graph.es):
            _orientations[i] = edge["pts"][0] - edge["pts"][-1]

        if network._2d:
            _orientations = np.hstack(
                (_orientations, np.zeros((len(_orientations), 1)))
            )

        nematic = freud.order.Nematic()
        nematic.compute(_orientations[np.where(_orientations.any(axis=1))[0]])
        self._nematic = nematic
        self._orientations = _orientations

        angles = []
        if network._2d:
            for orientation in _orientations:
                angles.append(vector_to_angle(orientation))
            self._angles = angles
        else:
            self._angles = None

    @_Compute._computed_property
    def nematic(self):
        r"""The :class:`freud.order.Nematic` compute module, populated with
        the nematic attributes. See the `freud documentation
        <https://freud.readthedocs.io/en/latest/order.html#freud.order.Nematic>`_
        for more information."""

        return self._nematic

    @_Compute._computed_property
    def nematic_order_parameter(self):
        r"""The nematic order parameter."""

        return self.nematic.order

    @_Compute._computed_property
    def nematic_tensor(self):
        r"""The nematic tensor."""

        return self.nematic.nematic_tensor

    @_Compute._computed_property
    def director(self):
        r"""The director."""

        return self.nematic.director

    @_Compute._computed_property
    def orientations(self):
        r"""The edge orientations."""

        return self._orientations

    @_Compute._computed_property
    def angles(self):
        r"""The angles that each edge makes with the x-axis. Only supported
        for 2D networks.
        """

        if self._angles is None:
            raise TypeError("Angles are not calculated for 3D networks.")
        else:
            return np.array(list(map(vector_to_angle, self._orientations)))
