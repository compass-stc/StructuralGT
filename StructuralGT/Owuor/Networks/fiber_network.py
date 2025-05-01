# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import copy
import json
import os
import time
import igraph
import sknw
import warnings
import cv2 as cv
# import gsd.hoomd
# import igraph as ig
import networkx as nx
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
# import scipy
from matplotlib.colorbar import Colorbar
from skimage.morphology import skeletonize
from mpl_toolkits.axes_grid1 import make_axes_locatable
from skimage.morphology import remove_small_objects

# from . import base

from ..SGT.base_image import BaseImage
from ..SGT.graph_skeleton import GraphSkeleton
from ..SGT.network_processor import ALLOWED_IMG_EXTENSIONS
from ..SGT.sgt_utils import write_gsd_file

"""
Questions for Alain:
    1. How do you make node_plots of 3D (your code crashes)?
    2. What is rotate (in set_graph)? It is created in img_to_skel.
"""

class FiberNetwork:
    """Generic class to represent networked image data.

    Args:
        directory (str):
            The (absolute or relative) pathname for the image(s) to be
            analysed. Where 2D analysis is concerned, the directory should
            contain a single image.
        binarized_dir (str):
            The pathname relative to directory for storing the binarized
            stack of images and all subsequent results.
        depth (tuple, optional):
            The file range from which files should be extracted from the
            directory. This is primarily used to analyse a subset of a large
            directory. Cropping can be carried out after, if this argument
            is not specified.
    """

    def __init__(self, directory, binarized_dir="Binarized", depth=None, prefix=None, dim=2):
        if dim == 2 and depth is not None:
            """Raised when incompatible combination of arguments is passed."""
            raise ValueError( "Cannot specify depth argument for 2D networks. Change dim to 3 if "
                                                    "you would like a single slice of a 3D network.")

        self.dir = directory
        self.binarized_dir = "/" + binarized_dir
        self.stack_dir = os.path.normpath(self.dir + self.binarized_dir)
        self.depth = depth
        self.dim = 2
        self._2d = True if self.dim == 2 else False
        self.prefix = "slice" if prefix is None else prefix

        # image_stack = _image_stack()
        image_stack = {}
        allowed_extensions = tuple(ext[1:] if ext.startswith('*.') else ext for ext in ALLOWED_IMG_EXTENSIONS)
        for slice_name in sorted(os.listdir(self.dir)):
            # fname = _fname(self.dir + "/" + slice_name, depth=depth, _2d=self._2d)
            img_path = self.dir + "/" + slice_name
            slice_num = FiberNetwork.verify_slice_number(img_path, self._2d)
            is_img = slice_name.endswith(allowed_extensions)
            contains_prefix = True if prefix is None else prefix in os.path.splitext(os.path.basename(img_path))[0]
            is_in_range = True if (is_img and self._2d) else False
            if not is_in_range and depth is not None:
                is_in_range = (depth[0] < int(slice_num) < depth[1])

            if dim == 2 and is_img and contains_prefix:
                if len(image_stack.items()) != 0:
                    warnings.warn( "You have specified a 2D network but there are several suitable images in the given "
                                   "directory. By default, StructuralGT will take the first image. To override, "
                                   "specify the prefix argument.")
                    break
                _slice = plt.imread(self.dir + "/" + slice_name)
                # image_stack.append(_slice, slice_name)
                image_stack[slice_name] = _slice
            if dim == 3:
                if is_in_range and contains_prefix:
                    _slice = plt.imread(self.dir + "/" + slice_name)
                    # image_stack.append(_slice, slice_name)
                    image_stack[slice_name] = _slice

        self.image_stack = image_stack
        # self.image_stack.package()
        # if len(self.image_stack) == 0:
        if len(self.image_stack.items()) == 0:
            raise ImageDirectoryError(self.stack_dir)

    def binarize(self, options="img_options.json", crop: list=None):
        """Binarizes stack of experimental images using a set of image
        processing parameters.

        Args:
            options (dict, optional):
                A dictionary of option-value pairs for image processing. All
                options must be specified. When this argument is not
                specified, the network's parent directory will be searched for
                a file called img_options.json, containing the options.
            crop (list):
                The x, y and (optionally) z coordinates of the cuboid/
                rectangle which encloses the :class:`Network` region of
                interest.
        """
        if not os.path.isdir(self.dir + self.binarized_dir):
            os.mkdir(self.dir + self.binarized_dir)

        if isinstance(options, str):
            options = self.dir + "/" + options
            with open(options) as f:
                options = json.load(f)
        elif not isinstance(options, dict):
            try:
                options.predict(self)
                return
            except ImportError:
                raise TypeError("The options argument must be a str, dict, or deeplearner. If it is a deeplearner, "
                                "you must have tensorflow installed.")

        self.cropper = _cropper(self, domain=crop)
        if self._2d:
            img_bin = np.zeros(self.cropper.dims)
        else:
            img_bin = np.zeros(self.cropper.dims)
            img_bin = np.swapaxes(img_bin, 0, 2)
            img_bin = np.swapaxes(img_bin, 1, 2)


        # for _, name in self.image_stack:
        i = self.cropper.surface
        for name in self.image_stack.keys():
            # fname = _fname(self.dir + "/" + name, _2d=self._2d)
            img_path = self.dir + "/" + name
            slice_num = FiberNetwork.verify_slice_number(img_path, self._2d)
            gray_image = cv.imread(self.dir + "/" + name, cv.IMREAD_GRAYSCALE)
            # _, img_bin, _ = process_image.binarize(gray_image, options)
            img_obj = BaseImage(gray_image)
            img_data = img_obj.img_2d.copy()
            img_obj.img_mod = img_obj.process_img(image=img_data)
            img_obj.img_bin = img_obj.binarize_img(img_obj.img_mod.copy())

            plt.imsave(self.stack_dir + "/" + self.prefix + slice_num + ".tiff", img_obj.img_bin, cmap=mpl.cm.gray)

            img_bin[i - self.cropper.surface] = img_obj.img_bin[self.cropper._2d] / 255
            i += 1

        # For 2D images, img_bin_3d.shape[0] == 1
        # Always 3d, even for 2d images
        self._img_bin_3d = img_bin
        # 3d for 3d images, 2d otherwise
        self._img_bin = np.squeeze(img_bin)

    def img_to_skel( self, graph_options, img_options="img_options.json" ):
        """Writes calculates and writes the skeleton to a :code:`.gsd` file.

        Note: if the rotation argument is given, this writes the union of all
        of the graph which can be obtained from cropping after rotation about
        the origin. The rotated skeleton can be written after the :attr:`graph`
        attribute has been set.

        Args:
            img_options (dict, optional):
                A dictionary of option-value pairs for image processing. All
                options must be specified. When this argument is not
                specified, the network's parent directory will be searched for
                a file called img_options.json, containing the options.
            name (str):
                File name to write.
            crop (list):
                The x, y and (optionally) z coordinates of the cuboid/
                rectangle which encloses the :class:`Network` region of
                interest.
            skeleton (bool):
                Whether to write the skeleton or the unskeletonized
                binarization of the image(s).
            rotate (float):
                The amount to rotate the skeleton by *after* the
                :py:attr:`Gr` attribute has been set.
            debubble (list[:class:`numpy.ndarray`]):
                The footprints to use for a debubbling protocol.
            box (bool):
                Whether to plot the boundaries of the cropped
                :class:`Network`.
            merge_nodes (int):
                The radius of the disk used in the node merging protocol,
                taken from :cite:`Vecchio2021`.
            prune (int):
                The number of times to apply the pruning algorithm taken from
                :cite:`Vecchio2021`.
            remove_objects (int):
                The size of objects to remove from the skeleton, using the
                algorithm in :cite:`Vecchio2021`.
        """

        if graph_options["crop"] is not None and self.depth is not None:
            if graph_options["crop"][4] < self.depth[0] or graph_options["crop"][5] > self.depth[1]:
                raise ValueError("crop argument cannot be outwith the bounds of the network's depth")
        if graph_options["crop"] is not None and self.depth is None and not self._2d:
            # if len(self.image_stack) < crop[5] - crop[4]:
            if len(self.image_stack.items()) < graph_options["crop"][5] - graph_options["crop"][4]:
                raise ValueError("Crop too large for image stack")
            else:
                self.depth = [graph_options["crop"][4], graph_options["crop"][5]]

        start = time.time()

        # self.gsd_name = _abs_path(self, name)
        if graph_options["file"][0] == "/":
            self.gsd_name = graph_options["file"]
        else:
            self.gsd_name = self.stack_dir + "/" + graph_options["file"]

        self.gsd_dir = os.path.split(self.gsd_name)[0]

        # self.set_img_bin(crop)
        self.binarize(img_options, graph_options["crop"])

        if graph_options["skeleton"]:
            self._skeleton = skeletonize(np.asarray(self._img_bin, dtype=np.dtype("uint8")))
            self.skeleton_3d = skeletonize(np.asarray(self._img_bin_3d, dtype=np.dtype("uint8")))
        else:
            self._img_bin = np.asarray(self._img_bin)
            self.skeleton_3d = self._img_bin_3d
            self._skeleton = self._img_bin

        if graph_options["debubble"] is not None:
            # self = base.debubble(self, debubble)
            self._skeleton = GraphSkeleton.remove_bubbles(self._img_bin, graph_options["debubble"])
            print(f"Ran debubble for an image with shape {self._skeleton.shape}")

        if graph_options["merge_nodes"]:
            # self = base.merge_nodes(self, merge_nodes)
            self._skeleton = GraphSkeleton.merge_nodes(self._skeleton)
            print(f"Ran merge_nodes for an image with shape {self._skeleton.shape}")

        if graph_options["prune"] is not None:
            # self = base.prune(self, prune)
            b_points = GraphSkeleton.get_branched_points(self._skeleton)
            self._skeleton = GraphSkeleton.prune_edges(self._skeleton, 500, b_points)
            print(f"Ran prune for an image with shape {self._skeleton.shape}")

        if graph_options["remove_objects"] is not None:
            # self = base.remove_objects(self, remove_objects)
            canvas = self._skeleton
            self._skeleton = remove_small_objects(canvas, graph_options["remove_objects"], connectivity=2)
            # gsd_file = self.gsd_dir + "/cleaned_" + os.path.split(self.gsd_name)[1]
            # write_gsd_file(gsd_file, self.skeleton_3d)
            print(f"Ran remove objects for an image with shape {self._skeleton.shape}")
        self.skeleton_3d = np.asarray(self._skeleton)
        if self._2d:
            self.skeleton_3d = np.asarray([self._skeleton])

        # Save to GSD/HOOMD file
        gsd_file = self.gsd_dir + "/" + os.path.split(self.gsd_name)[1]
        write_gsd_file(gsd_file, self.skeleton_3d)

        positions = np.asarray(np.where(np.asarray(self.skeleton_3d) == 1)).T
        """self.shape = np.asarray(list(max(positions.T[i]) + 1 for i in (2, 1, 0)[0: self.dim]))
        self.positions = positions
        with gsd.hoomd.open(name=self.gsd_name, mode="w") as f:
            s = gsd.hoomd.Frame()
            s.particles.N = len(positions)
            if box:
                L = list(max(positions.T[i]) for i in (0, 1, 2))
                s.particles.position, self.shift = base.shift(positions, _shift=(L[0] / 2, L[1] / 2, L[2] / 2))
                s.configuration.box = [L[0], L[1], L[2], 0, 0, 0]
            else:
                s.particles.position, self.shift = base.shift(positions)
            s.particles.types = ["A"]
            s.particles.typeid = ["0"] * s.particles.N
            f.append(s)"""
        end = time.time()
        print("Ran img_to_skel() and cleaned in ", end - start, "for skeleton with ", len(positions), "voxels")

    def set_graph(self, sub=True, weight_type=None, **kwargs):
        """Sets :class:`Graph` object as an attribute by reading the
        skeleton file written by :meth:`img_to_skel`.

        Args:
            sub (optional, bool):
                Whether to onlyh assign the largest connected component as the
                :class:`igraph.Graph` object.
            weight_type (optional, str):
                How to weight the edges. Options include :code:`Length`,
                :code:`Width`, :code:`Area`,
                :code:`FixedWidthConductance`,
                :code:`VariableWidthConductance`,
                :code:`PerpBisector`.
        """

        if not hasattr(self, '_skeleton'):
            raise AttributeError("Network has no skeleton. You should call img_to_skel before calling set_graph.")
        # self.Gr = base.gsd_to_G(self.gsd_name)

        print("Running build_sknw ...")
        img_skel = self.skeleton_3d.astype(int)  # DOES NOT PLOT - node_plot (BUG IN CODE), so we pick first image in stack
        selected_slice = 0  # Select first slice in 3D skeleton of shape (depth, w, h)

        # G = sknwEdits.build_sknw(img_skel[selected_slice])
        # nx_3d_graph = G.to_networkx()
        nx_graph = sknw.build_sknw(img_skel[selected_slice])
        G = igraph.Graph.from_networkx(nx_graph)

        # Compute avg. degree from nx
        degree_arr = np.array(list(dict(nx.degree(nx_graph)).values()))
        print(f"NetworkX Avg. Degree: {np.mean(degree_arr)}")

        self.Gr = G   # For Testing
        if sub:
            print(f"Before removing smaller components, graph has {G.vcount()}  nodes")
            components = G.connected_components()
            G = components.giant()
            print(f"After removing smaller components, graph has {G.vcount()}  nodes")
        # self.Gr = G

        if weight_type is not None:
            # self.Gr = base.add_weights(self, weight_type=weight_type, **kwargs)
            _img_bin = self._img_bin  # [self.shift[0][1]::, self.shift[0][2]::]
            if not isinstance(weight_type, list):
                raise TypeError("weight_type must be list, even if single element")

            for _type in weight_type:
                print(_type)
                for i, edge in enumerate(self.Gr.es()):
                    ge = edge["pts"]
                    graph_skel = GraphSkeleton(img_bin=_img_bin)
                    pix_width, pix_angle, wt = graph_skel.assign_weights(ge)
                    if _type == "VariableWidthConductance" or _type == "FixedWidthConductance":
                        _type_name = "Conductance"
                    else:
                        _type_name = _type
                    edge["pixel width"] = pix_width
                    edge[_type_name] = wt
            print("Finished with weight_type ", weight_type)

        self.shape = list(max(list(self.Gr.vs[i]["o"][j] for i in range(self.Gr.vcount())))
            for j in (0, 1, 2)[0: self.dim])

    def node_plot(self, parameter=None, ax=None, depth=0):
        """Superimpose the skeleton, image, and nodal graph theory parameters.
        If no parameter provided, simply imposes skeleton and image.

        Args:
            parameter (:class:`numpy.ndarray`, optional):
                The value of node parameters
            ax (:class:`matplotlib.axes.Axes`, optional):
                Axis to plot on. If :code:`None`, make a new figure and axis.
                (Default value = :code:`None`)
            depth (int, optional): If the network is 3D, which slice to plot.

        Returns:
            (:class:`matplotlib.axes.Axes`): Axis with the plot.
        """

        _parameter = True
        if parameter is None:
            parameter = np.ones(self.Gr.vcount(), dtype=np.intc)
            _parameter = False

        assert self.Gr.vcount() == len(parameter)

        if ax is None:
            fig = plt.figure()
            ax = fig.subplots()

        ax.set_xticks([])
        ax.set_yticks([])
        # img = self.image_stack[depth][0][self.cropper._2d]
        key_list = list(self.image_stack.keys())
        key_at_index = key_list[depth]
        img = self.image_stack[key_at_index][self.cropper._2d]
        ax.imshow(img, cmap="gray")

        e = np.empty((0, 2))
        for edge in self.Gr.es:
            e = np.vstack((e, edge["pts"]))
        ax.scatter(e.T[1], e.T[0], c="k", s=3, marker="s", edgecolors="none")

        y, x = np.array(self.Gr.vs["o"]).T
        sp = ax.scatter(
            x,
            y,
            c=parameter,
            s=10,
            marker="o",
            cmap="plasma",
            edgecolors="none",
        )

        if _parameter:
            cb = FiberNetwork.colorbar(sp, ax)
            cb.set_label("Value")

        return ax

    def edge_plot(self, parameter=None, ax=None, depth=0, edge_cmap="plasma", plot_img=True, **kwargs, ):
        """Superimpose the skeleton, image, and nodal graph theory parameters.
        If no parameter provided, simply imposes skeleton and image.

        Args:
            parameter (:class:`numpy.ndarray`, optional):
                The value of node parameters
            ax (:class:`matplotlib.axes.Axes`, optional):
                Axis to plot on. If :code:`None`, make a new figure and axis.
                (Default value = :code:`None`)

        Returns:
            (:class:`matplotlib.axes.Axes`): Axis with the plot.
        """

        _parameter = True
        if parameter is None:
            parameter = np.ones(self.Gr.ecount(), dtype=np.intc)
            _parameter = False

        assert self.Gr.ecount() == len(parameter)

        if ax is None:
            fig = plt.figure()
            ax = fig.subplots()

        ax.set_xticks([])
        ax.set_yticks([])
        if plot_img:
            # img = self.image_stack[depth][0][self.cropper._2d]
            key_list = list(self.image_stack.keys())
            key_at_index = key_list[depth]
            img = self.image_stack[key_at_index][self.cropper._2d]
            ax.imshow(img, cmap="gray")
        _max = np.max(parameter)
        _min = np.min(parameter)

        for param, edge in zip(parameter, self.Gr.es):
            e = edge["pts"].T
            ax.scatter(
                e[1],
                e[0],
                s=3,
                marker="s",
                edgecolors="none",
                c=[
                    param,
                ]
                * len(edge["pts"]),
                vmin=_min,
                vmax=_max,
                cmap=edge_cmap,
                **kwargs,
            )

        y, x = np.array(self.Gr.vs["o"]).T
        ax.scatter(x, y, s=10, marker="o", edgecolors="none", c="red")

        norm = mpl.colors.Normalize(vmin=_min, vmax=_max)
        mappable = mpl.cm.ScalarMappable(norm=norm, cmap=edge_cmap)
        if _parameter:
            cb = FiberNetwork.colorbar(mappable, ax)
            cb.set_label("Value")

        return fig, ax

    def recon(self, axis, surface, depth):
        """Method displays 2D slice of binary image and
        annotates with attributes from 3D graph subslice
        """

        Gr_copy = copy.deepcopy(self.Gr)

        # self.Gr = base.sub_G(self.Gr)

        axis_0 = abs(axis - 2)

        np.swapaxes(self._img_bin_3d, 0, axis_0)[surface]
        drop_list = []
        for i in range(self.Gr.vcount()):
            if (
                self.Gr.vs[i]["o"][axis_0] < surface
                or self.Gr.vs[i]["o"][axis_0] > surface + depth
            ):
                drop_list.append(i)
                continue

        self.Gr.delete_vertices(drop_list)

        node_positions = np.asarray(
            list(self.Gr.vs()[i]["o"] for i in range(self.Gr.vcount()))
        )
        positions = np.array([[0, 0, 0]])
        for edge in self.Gr.es():
            positions = np.vstack((positions, edge["pts"]))

        plt.figure(figsize=(10, 25))
        plt.scatter(node_positions.T[2], node_positions.T[1], s=10,
                    color="red")
        plt.scatter(positions.T[2], positions.T[1], s=2)
        plt.imshow(self._img_bin[axis], cmap=mpl.cm.gray)
        plt.show()

        self.Gr = Gr_copy

    @staticmethod
    def colorbar(mappable, ax, *args, **kwargs):
        # ax = mappable.axes
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cbar = Colorbar(cax, mappable)
        ax.set(*args, **kwargs)
        return cbar

    @staticmethod
    def verify_slice_number(f_name, is_2d=False):
        """Slice filenames must end in 4 digits, indicating the depth of the slice."""
        if not os.path.exists(f_name):
            raise ValueError("File does not exist.")

        if is_2d:
            num = "0000"
        else:
            base_name = os.path.splitext(os.path.split(f_name)[1])[0]
            if len(base_name) < 4:
                raise ValueError("For 3D networks, filenames must end in 4 digits, indicating the depth of the slice.")
            num = base_name[-4::]

            if not num.isnumeric():
                raise ValueError("For 3D networks, filenames must end in 4 digits, indicating the depth of the slice.")
        return num


class _cropper:
    """Cropper class contains methods to deal with images of different
    dimensions and their geometric modifications. Generally there is no need
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
            # Strip file type and 'slice' then convert to int
            slice_name = next(iter(Network.image_stack.keys()))  # Only first item
            img_path = Network.dir + "/" + slice_name
            slice_num = FiberNetwork.verify_slice_number(img_path)
            self.surface = int(slice_num)
        else:
            self.surface = domain[4]
        if Network._2d:
            depth = 1
        else:
            if domain is None:
                # depth = len(Network.image_stack)
                depth = len(Network.image_stack.items())
            else:
                depth = domain[5] - domain[4]
            if depth == 0:
                raise ImageDirectoryError(Network.stack_dir)
        self.depths = Network.depth

        if domain is None:
            self.domain = None
            self.crop = slice(None)
            img_arr = next(iter(Network.image_stack.values()))  # Only first item
            # planar_dims = Network.image_stack[0][0].shape[0:2]
            planar_dims = img_arr.shape[0:2]
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
        integers such that the new crop contains at least all the space
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



class ImageDirectoryError(ValueError):
    """Raised when a directory is accessed but does not have any images"""

    def __init__(self, directory_name):
        self.directory_name = directory_name

    def __str__(self):
        """Returns the error message"""
        return f"The directory {self.directory_name} has no suitable images. You may need to specify the prefix argument."




