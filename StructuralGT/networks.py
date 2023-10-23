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

from util import *

class Network:
    """Generic class to represent networked image data. Should not be
    instantiated by the user.

    Children of this class will hold igraph :class:`Graph` attributes and
    holds additional attributes and methods for supporting geometric features
    associated images, dimensionality etc.

    Args:
        directory (str):
            The (absolute or relative) pathname for the stack of images to be
            analysed. Where 2D analysis is concerned, the directory should
            contain a single image.
        child_dir (str):
            The pathname relative to directory for storing the binarized 
            stack of images and all subsequent results.
        depth (tuple, optional):
            The file range from which files should be extracted from the 
            directory. This is primarily used to analyse a subset of a large
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
                _slice = cv.imread(self.dir + "/" + slice_name)
                image_stack.append(_slice, slice_name)

        self.image_stack = image_stack
        self.image_stack.package()
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

        for _,name in self.image_stack:
            fname = _fname(self.dir + '/' + name)
            gray_image = cv.imread(self.dir + '/' + name, cv.IMREAD_GRAYSCALE)
            _, img_bin, _ = process_image.binarize(gray_image, options_dict)
            plt.imsave(
                self.stack_dir + "/slice" + fname.num + ".tiff",
                img_bin,
                cmap=cm.gray,
            )

        self.options = options_dict

    def set_img_bin(self, crop):
        """Sets the :attr:`img_bin` and :attr:`img_bin_3d` attributes, which
        are numpy arrays of pixels and voxels which represent the binarized 
        image. Called internally by child classes of :class:`Network`.

        Args:
            crop (list):
                The x, y and (optionally) z coordinates of the cuboid/
                rectangle which encloses the :class:`Network` region of
                interest.
        """
        self.cropper = _cropper(self, domain=crop)
        if self._2d:
            img_bin = np.zeros(self.cropper.dims)
        else:
            img_bin = np.zeros(self.cropper.dims)
            img_bin = np.swapaxes(img_bin, 0, 2)
            img_bin = np.swapaxes(img_bin, 1, 2)

        i = self.cropper.surface
        for fname in sorted(os.listdir(self.stack_dir)):
            fname = _fname(self.stack_dir + "/" + fname, 
                           domain=_domain(self.cropper._3d))
            if fname.isimg and fname.isinrange:
                suff = base.quadrupletise(i)
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
        self._img_bin_3d = img_bin
        self._img_bin = img_bin

        # Always 3d, even for 2d images
        self._img_bin_3d = self._img_bin
        # 3d for 3d images, 2d otherwise
        self._img_bin = np.squeeze(self._img_bin)

    @property
    def img_bin(self):
        """:class:`np.ndarray`: The binary image from which the graph was 
        extracted"""
        return self._img_bin

    @img_bin.setter
    def img_bin(self, value):
        warnings.warn("Setting the binary image should not be necessary if \
                      the raw data has been binarized.")

    @property
    def graph(self):
        """:class:`igraph.Graph`: The Graph object extracted from the 
        skeleton"""
        return self.Gr


