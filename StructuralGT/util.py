import numpy as np
import os
import cv2 as cv
from StructuralGT import error, base, process_image
import json
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import time
import gsd.hoomd
import warnings

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
        if domain is None or Network._2d:
            self.surface = int(
                _fname(Network.dir + '/' + Network.image_stack[0][1]).num
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
            self.crop = slice(None)
            planar_dims = cv.imread(
                Network.stack_dir + "/slice0000.tiff",
                cv.IMREAD_GRAYSCALE).shape
            if self.dim == 2:
                self.dims = (1,) + planar_dims
            else:
                self.dims = planar_dims + (depth,)

        else:
            if self.dim == 2:
                self.crop = (slice(domain[2], domain[3]),
                             slice(domain[0], domain[1]))
                self.dims = (1, domain[3] - domain[2], domain[1] - domain[0])

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
        which crops the square associated with the :class:`Network` space.
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
            raise ValueError('Only 2D crops are supported')
        if self.crop == slice(None):
            raise ValueError('No crop associated with this _cropper')

        centre = (
            self.crop[0].start + 0.5 * (self.crop[0].stop - self.crop[0].start),
            self.crop[1].start + 0.5 * (self.crop[1].stop - self.crop[1].start),
        )

        diagonal = ((self.crop[0].stop - self.crop[0].start) ** 2
                    + (self.crop[1].stop - self.crop[1].start) ** 2) ** 0.5

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


class _domain():
    """Helper class which returns an infinitely large space when no explicit
    space is associated with the :class:`_domain`
    """

    def __init__(self, domain):
        if domain is None:
            self.domain = [-np.inf, np.inf]
        else:
            self.domain = domain


class _fname():
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

    def __init__(self, name, domain=_domain(None)):
        if not os.path.exists(name):
            raise ValueError('File does not exist.')
        self.name = name
        self.domain = domain
        num1 = name[-8:-4]
        num2 = name[-9:-5]
        if num1.isnumeric() and num2.isnumeric():
            raise ValueError('Directory contents names ambiguous.')
        elif num1.isnumeric():
            self.num = num1
        elif num2.isnumeric():
            self.num = num2
        else:
            self.num = 'Non-numeric'

    @property
    def isnumeric(self):
        """bool: Whether the filename is numeric."""
        return self.num.isnumeric()

    @property
    def isinrange(self):
        """bool: Returns true iff the filename is numeric and within the
        spatial dimensions of the associated :class:`_domain` object.
        """
        if not self.isnumeric:
            return False
        else:
            return (int(self.num) > self.domain.domain[0]
                and int(self.num) < self.domain.domain[1])

    @property
    def isimg(self):
        """bool: Returns true iff the filename suffix is a supported image
        file type.
        """
        return base.Q_img(self.name)

