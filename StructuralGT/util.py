# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import os
from functools import wraps

import numpy as np

from StructuralGT import base, error


class _Compute:
    r"""Parent class for all compute classes in StructuralGT. Modelled after
    the :class:`_Compute` class used in **freud** :cite:`Ramasubramani2020`.

    The primary purpose of this class is to prevent access of uncomputed
    values. This is accomplished by maintaining a boolean flag to track whether
    the compute method in a class has been called and decorating class
    properties that rely on compute having been called.

    To use this class, one would write, for example,

    .. code-block:: python
        class Electronic(_Compute):

            def compute(...)
                ...

            @_Compute._computed_property
            def effectice_resistance(self):
                return ...

    Attributes:
        _called_compute (bool):
            Flag representing whether the compute method has been called.
    """

    def __init__(self, node_weight=None, edge_weight=None):
        self._called_compute = False
        self.node_weight = node_weight
        self.edge_weight = edge_weight

    def __getattribute__(self, attr):
        """Compute methods set a flag to indicate that quantities have been
        computed. Compute must be called before plotting."""
        attribute = object.__getattribute__(self, attr)
        if attr == "compute":
            # Set the attribute *after* computing. This enables
            # self._called_compute to be used in the compute method itself.
            compute = attribute

            @wraps(compute)
            def compute_wrapper(*args, **kwargs):
                return_value = compute(*args, **kwargs)
                self._called_compute = True
                return return_value

            return compute_wrapper
        elif attr == "plot":
            if not self._called_compute:
                raise AttributeError(
                    "The compute method must be called before calling plot."
                )
        return attribute

    @staticmethod
    def _computed_property(prop):
        r"""Decorator that makes a class method to be a property with limited
        access.

        Args:
            prop (callable): The property function.

        Returns:
            Decorator decorating appropriate property method.
        """

        @property
        @wraps(prop)
        def wrapper(self, *args, **kwargs):
            if not self._called_compute:
                raise AttributeError(
                    "Property not computed. Call compute \
                                     first."
                )
            return prop(self, *args, **kwargs)

        return wrapper


def _abs_path(network, name):
    if name[0] == "/":
        return name
    else:
        return network.stack_dir + "/" + name


class _image_stack:
    """Class for holding images and the names of their respective files"""

    def __init__(self):
        self._images = []
        self._slice_names = []
        self._index = -1

    def append(self, _slice, _slice_name):
        self._images.append(_slice)
        self._slice_names.append(_slice_name)

    def __getitem__(self, key):
        return (self._images[key], self._slice_names[key])

    def package(self):
        self._images = np.asarray(self._images)

    def __len__(self):
        return len(self._images)

    def __iter__(self):
        return self

    def __next__(self):
        self._index += 1
        if self._index >= len(self):
            self._index = -1
            raise StopIteration
        else:
            return self._images[self._index], self._slice_names[self._index]


class _cropper:
    """Cropper class contains methods to deal with images of different
    dimensions and their geometric modificaitons. Generally there is no need
    for the user to instantiate this directly.

    Args:
        Network (:class:`Network`:):
            The :class:`Network` object to which the cropper is associated
            with
        domain (list):
            The corners of the cuboid/rectangle which enclose the network's
            region of interest
    """

    def __init__(self, Network, domain=None):
        self.dim = Network.dim
        if Network._2d:
            self.surface = 0
        elif domain is None:
            self.surface = int(
                _fname(Network.dir + "/" + Network.image_stack[0][1]).num
            )  # Strip file type and 'slice' then convert to int
        else:
            self.surface = domain[4]
        if Network._2d:
            depth = 1
        else:
            if domain is None:
                depth = len(Network.image_stack)
            else:
                depth = domain[5] - domain[4]
            if depth == 0:
                raise error.ImageDirectoryError(Network.stack_dir)
        self.depths = Network.depth

        if domain is None:
            self.domain = None
            self.crop = slice(None)
            planar_dims = Network.image_stack[0][0].shape[0:2]
            if self.dim == 2:
                self.dims = (1,) + planar_dims
            else:
                self.dims = planar_dims + (depth,)

        else:
            if self.dim == 2:
                self.crop = (slice(domain[2], domain[3]),
                             slice(domain[0], domain[1]))
                self.dims = (1, domain[3] - domain[2], domain[1] - domain[0])
                self.domain = (domain[2], domain[3], domain[0], domain[1])

            else:
                self.crop = (
                    slice(domain[0], domain[1]),
                    slice(domain[2], domain[3]),
                    slice(domain[4], domain[5]),
                )
                self.dims = (
                    domain[1] - domain[0],
                    domain[3] - domain[2],
                    domain[5] - domain[4],
                )
                self.domain = (
                    domain[0],
                    domain[1],
                    domain[2],
                    domain[3],
                    domain[4],
                    domain[5],
                )

    @classmethod
    def from_string(cls, Network, domain):
        if domain == "None":
            return cls(Network, domain=None)
        else:
            domain = domain.split(",")
        if len(domain) == 4:
            _0 = int(domain[0][1:])
            _1 = int(domain[1])
            _2 = int(domain[2])
            _3 = int(domain[3][:-1])
            return cls(Network, domain=[_0, _1, _2, _3])

    def intergerise(self):
        """Method casts decimal values in the _croppers crop attribute to
        integers such that the new crop contains at least all of the space
        enclosed by the old crop
        """
        first_x = np.floor(self.crop[0].start).astype(int)
        last_x = np.ceil(self.crop[0].stop).astype(int)

        first_y = np.floor(self.crop[1].start).astype(int)
        last_y = np.ceil(self.crop[1].stop).astype(int)

        if self.dim == 2:
            self.crop = slice(first_x, last_x), slice(first_y, last_y)
            self.dims = (1, last_x - first_x, last_y - first_y)
        else:
            first_z = np.floor(self.crop[2].start).astype(int)
            last_z = np.ceil(self.crop[2].stop).astype(int)
            self.crop = (
                slice(first_x, last_x),
                slice(first_y, last_y),
                slice(first_z, last_z),
            )

    def __str__(self):
        return str(self.domain)

    @property
    def _3d(self):
        if self.dim == 2:
            return None
        elif self.crop == slice(None):
            return self.depths
        else:
            return [self.crop[2].start, self.crop[2].stop]

    @property
    def _2d(self):
        """list: If a crop is associated with the object, return the component
        which crops the rectangle associated with the :class:`Network` space.
        """
        if self.crop == slice(None):
            return slice(None)
        else:
            return self.crop[0:2]

    @property
    def _outer_crop(self):
        """Method supports square 2D crops only. It calculates the crop which
        could contain any rotation about the origin of the _cropper's crop
        attribute.

        Returns:
            (list): The outer crop
        """

        if self.dim != 2:
            raise ValueError("Only 2D crops are supported")
        if self.crop == slice(None):
            raise ValueError("No crop associated with this _cropper")

        centre = (
            self.crop[0].start + 0.5 *
            (self.crop[0].stop - self.crop[0].start),
            self.crop[1].start + 0.5 *
            (self.crop[1].stop - self.crop[1].start),
        )

        diagonal = (
            (self.crop[0].stop - self.crop[0].start) ** 2
            + (self.crop[1].stop - self.crop[1].start) ** 2
        ) ** 0.5

        outer_crop = np.array(
            [
                centre[0] - diagonal * 0.5,
                centre[0] + diagonal * 0.5,
                centre[1] - diagonal * 0.5,
                centre[1] + diagonal * 0.5,
            ],
            dtype=int,
        )

        return outer_crop


class _domain:
    """Helper class which returns an infinitely large space when no explicit
    space is associated with the :class:`_domain`
    """

    def __init__(self, domain):
        if domain is None:
            self.domain = [-np.inf, np.inf]
        else:
            self.domain = domain


class _fname:
    """Class to represent file names of 2D image slices, with helper
    functions.

    Assumes each file has 4 character number, e.g. 0053, followed by 3 or 4
    character extension, e.g. .tif or .tiff.

    Args:
        name (str):
            The name of the file.
        domain (_domain):
            The spatial dimensions of the associated Network object.
    """

    def __init__(self, name, domain=_domain(None), _2d=False):
        if not os.path.exists(name):
            raise ValueError("File does not exist.")
        self.name = name
        self.domain = domain
        self._2d = _2d

        if self._2d:
            self.num = "0000"
        else:
            base_name = os.path.splitext(os.path.split(self.name)[1])[0]
            if len(base_name) < 4:
                raise ValueError(
                    "For 3D networks, filenames must end in 4 digits, \
                    indicating the depth of the slice."
                )
            self.num = base_name[-4::]

            if not self.num.isnumeric():
                raise ValueError(
                    "For 3D networks, filenames must end in 4 digits, \
                    indicating the depth of the slice."
                )

    @property
    def isinrange(self):
        """bool: Returns true iff the filename is numeric and within the
        spatial dimensions of the associated :class:`_domain` object.
        """
        if not self.isimg:
            return False

        if self._2d:
            return True
        else:
            return (
                int(self.num) > self.domain.domain[0]
                and int(self.num) < self.domain.domain[1]
            )

    @property
    def isimg(self):
        """bool: Returns true iff the filename suffix is a supported image
        file type.
        """
        return base.Q_img(self.name)

    def __contains__(self, item):
        if item is None:
            return True
        else:
            """str: Returns leading string of the filename."""
            return item in os.path.splitext(os.path.basename(self.name))[0]
