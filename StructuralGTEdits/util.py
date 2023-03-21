import numpy as np
import os
import cv2 as cv
from StructuralGTEdits import error, base, process_image, convert, sknwEdits
import json
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import time
import gsd.hoomd
from skimage.measure import regionprops, label
import copy


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

        if domain is None:
            self.crop = slice(None)
            planar_dims = cv.imread(
                Network.stack_dir + "/slice000.tiff",
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

    @property
    def _2d(self):
        """list: If a crop is associated with the object, return the component
        which crops the square associated with the :class:`Network` space.
        """
        if self.crop == slice(None):
            return slice(None)
        else:
            return self.crop[0:2]

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
    def _outer_crop(self):
        """Method supports square 2D crops only. It calculates the crop which
        could contain any rotation of the _cropper's crop attribute.

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

    Assumes each file has 3 character number, e.g. 053, followed by 3 or 4
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
        num1 = name[-7:-4]
        num2 = name[-8:-5]
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


class Network:
    """Generic class to represent networked image data.

    Children of this class will hold igraph :class:`Graph` attributes and
    holds additional attributes and methods for supporting geometric features
    associated images,dimensionality etc.

    Args:
        directory (str):
            The (absolute or relative) pathname for the stack of images to be
            analysed. Where 2D analysis is concerned, the directory should
            contain a single image.
        child_dir (str):
            The relative pathname for storing the binarized stack of images
            and all subsequent results.
        depth (tuple, optional):
            The file range from which should be extracted from the directory
            files. This is primarily used to analyse a subset of a very large
            directory. Cropping can be carried out after, if this argument
            is not specified.
    """

    def __init__(self, directory, child_dir="Binarized", depth=None):

        self.dir = directory
        self.child_dir = '/' + child_dir
        self.stack_dir = self.dir + self.child_dir
        self.depth = depth

        #self.img, self.slice_names = [], []
        image_stack = _image_stack()
        for slice_name in sorted(os.listdir(self.dir)):
            fname = _fname(self.dir + '/' + slice_name,
                           domain=_domain(depth))
            if (fname.isinrange and fname.isimg):
                _slice = cv.imread(self.dir + "/" + slice_name,
                                   cv.IMREAD_GRAYSCALE)
                image_stack.append(_slice, slice_name)
                #self.img.append(_slice)
                #self.slice_names.append(slice_name)

        self.image_stack = image_stack
        self.image_stack.package()
        #self.img = np.asarray(self.img)
        if len(self.image_stack)==1: 
            self._2d = True
            self.dim = 2
        else:
            self._2d = False
            self.dim = 3

    def binarize(self, options_dict=None):
        """Binarizes stack of experimental images using a set of image
        processing parameters.

        Args:
            options_dict (dict, optional):
                A dictionary of option-value pairs for image processing. All
                options must be specified. When this arguement is not
                specified, the network's parent directory will be searched for
                a file called img_options.json, containing the options.
        """

        if options_dict is None:
            options = self.dir + "/img_options.json"
            with open(options) as f:
                options_dict = json.load(f)

        if not os.path.isdir(self.dir + self.child_dir):
            os.mkdir(self.dir + self.child_dir)

        for image,name in self.image_stack:
            fname = _fname(self.dir + '/' + name)
            _, img_bin, _ = process_image.binarize(image, options_dict)
            plt.imsave(
                self.stack_dir + "/slice" + fname.num + ".tiff",
                img_bin,
                cmap=cm.gray,
            )

        self.options = options_dict


    def set_img_bin(self, crop):
        
        self.cropper = _cropper(self, domain=crop)
        # Initilise i such that it starts at the lowest number belonging
        # to the images in the stack_dir
        # First require boolean mask to filter out non image files
        if self._2d:
            img_bin = np.zeros(self.cropper.dims)
        else:
            img_bin = np.zeros(self.cropper.dims)
            img_bin = np.swapaxes(img_bin, 0, 2)
            img_bin = np.swapaxes(img_bin, 1, 2)

        i = self.cropper.surface
        for fname in sorted(os.listdir(self.stack_dir)):
            fname = _fname(self.stack_dir + "/" + fname, domain=_domain(self.depth))
            if fname.isimg and fname.isinrange:
                suff = base.tripletise(i)
                img_bin[i - self.cropper.surface] = (
                    base.read(
                        self.stack_dir + "/slice" + fname.num + ".tiff",
                        cv.IMREAD_GRAYSCALE,
                    )[self.cropper._2d]
                    / 255
                )
                i = i + 1
            else:
                continue

        # For 2D images, img_bin_3d.shape[0] == 1
        self.img_bin_3d = img_bin
        self.img_bin = img_bin

        # Always 3d, even for 2d images
        self.img_bin_3d = self.img_bin
        # 3d for 3d images, 2d otherwise
        self.img_bin = np.squeeze(self.img_bin)

