# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import copy
import json
import os
import time
import warnings
from collections.abc import Sequence

import cv2 as cv
import freud
import gsd.hoomd
import igraph as ig
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import scipy
from matplotlib.colorbar import Colorbar
from skimage.morphology import skeletonize

from StructuralGT import base, error, process_image
from StructuralGT.util import (_abs_path, _cropper, _domain, _fname,
                               _image_stack)


def colorbar(mappable, ax, *args, **kwargs):
    from mpl_toolkits.axes_grid1 import make_axes_locatable

    # ax = mappable.axes
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    cbar = Colorbar(cax, mappable)
    ax.set(*args, **kwargs)
    return cbar


class Network:
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

    def __init__(
        self,
        directory,
        binarized_dir="Binarized",
        depth=None,
        prefix=None,
        dim=2,
    ):
        if dim == 2 and depth is not None:
            raise error.InvalidArgumentsError(
                "Cannot specify depth arguement for 2D networks. \
                Change dim to 3 if you would like a single slice of a 3D \
                network."
            )

        self.dir = directory
        self.binarized_dir = "/" + binarized_dir
        self.stack_dir = os.path.normpath(self.dir + self.binarized_dir)
        self.depth = depth
        self.dim = 2
        if self.dim == 2:
            self._2d = True
        else:
            self._2d = False
        if prefix is None:
            self.prefix = "slice"
        else:
            self.prefix = prefix

        image_stack = _image_stack()
        for slice_name in sorted(os.listdir(self.dir)):
            fname = _fname(
                self.dir + "/" + slice_name,
                domain=_domain(depth),
                _2d=self._2d,
            )
            if dim == 2 and fname.isimg and prefix in fname:
                if len(image_stack) != 0:
                    warnings.warn(
                        "You have specified a 2D network but there are \
                        several suitable images in the given directory. \
                        By default, StructuralGT will take the first image.\
                        To override, specify the prefix argument."
                    )
                    break
                _slice = plt.imread(self.dir + "/" + slice_name)
                image_stack.append(_slice, slice_name)
            if dim == 3:
                if fname.isinrange and fname.isimg and prefix in fname:
                    _slice = plt.imread(self.dir + "/" + slice_name)
                    image_stack.append(_slice, slice_name)

        self.image_stack = image_stack
        self.image_stack.package()
        if len(self.image_stack) == 0:
            raise error.ImageDirectoryError(
                "There are no suitable images in the given directory. You \
                may need to specify the prefix argument."
            )

    def binarize(self, options="img_options.json"):
        """Binarizes stack of experimental images using a set of image
        processing parameters.

        Args:
            options (dict, optional):
                A dictionary of option-value pairs for image processing. All
                options must be specified. When this arguement is not
                specified, the network's parent directory will be searched for
                a file called img_options.json, containing the options.
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
                raise TypeError(
                    "The options argument must be a str, dict, or "
                    "deeplearner. If it is a deeplearner, you must have "
                    "tensorflow installed."
                    )

        for _, name in self.image_stack:
            fname = _fname(self.dir + "/" + name, _2d=self._2d)
            gray_image = cv.imread(self.dir + "/" + name, cv.IMREAD_GRAYSCALE)
            _, img_bin, _ = process_image.binarize(gray_image, options)
            if self._2d:
                fname.num = "0000"
            plt.imsave(
                self.stack_dir + "/" + self.prefix + fname.num + ".tiff",
                img_bin,
                cmap=mpl.cm.gray,
            )

    def set_img_bin(self, crop):
        """Sets the :attr:`img_bin` and :attr:`img_bin_3d` attributes, which
        are numpy arrays of pixels and voxels which represent the binarized
        image. Called internally by subclasses of :class:`Network`.

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
            fname = _fname(
                self.stack_dir + "/" + fname,
                domain=_domain(self.cropper._3d),
                _2d=self._2d,
            )
            if fname.isimg and fname.isinrange:
                img_bin[i - self.cropper.surface] = (
                    base.read(
                        self.stack_dir + "/" + self.prefix + fname.num +
                        ".tiff",
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

    def set_graph(self, sub=True, weight_type=None, write="network.gsd",
                  **kwargs):
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
            raise AttributeError("Network has no skeleton. You should call \
                                 img_to_skel before calling set_graph.")

        G = base.gsd_to_G(self.gsd_name, _2d=self._2d, sub=sub)

        self.Gr = G
        self.write_name = write

        if self.rotate is not None:
            centre = np.asarray(self.shape) / 2
            inner_length_x = (self.inner_cropper.dims[2]) * 0.5
            inner_length_y = (self.inner_cropper.dims[1]) * 0.5
            inner_crop = np.array(
                [
                    centre[0] - inner_length_x,
                    centre[0] + inner_length_x,
                    centre[1] - inner_length_y,
                    centre[1] + inner_length_y,
                ],
                dtype=int,
            )

            node_positions = np.asarray(
                list(self.Gr.vs[i]["o"] for i in range(self.Gr.vcount()))
            )
            node_positions = base.oshift(node_positions, _shift=centre)
            node_positions = np.vstack(
                (node_positions.T, np.zeros(len(node_positions)))
            ).T
            node_positions = np.matmul(node_positions, self.rotate).T[0:2].T
            node_positions = base.shift(node_positions, _shift=-centre)[0]

            drop_list = []
            for i in range(self.Gr.vcount()):
                if not base.isinside(np.asarray([node_positions[i]]),
                                     inner_crop):
                    drop_list.append(i)
                    continue

                self.Gr.vs[i]["o"] = node_positions[i]
                self.Gr.vs[i]["pts"] = node_positions[i]
            self.Gr.delete_vertices(drop_list)

            node_positions = np.asarray(
                list(self.Gr.vs[i]["o"] for i in range(self.Gr.vcount()))
            )
            final_shift = np.asarray(
                list(min(node_positions.T[i]) for i in (0, 1, 2)[0: self.dim])
            )
            edge_positions_list = np.asarray(
                list(
                    base.oshift(self.Gr.es[i]["pts"], _shift=centre)
                    for i in range(self.Gr.ecount())
                ),
                dtype=object,
            )
            for i, edge in enumerate(edge_positions_list):
                edge_position = np.vstack((edge.T, np.zeros(len(edge)))).T
                edge_position = np.matmul(edge_position, self.rotate).T[0:2].T
                edge_position = base.shift(edge_position,
                                           _shift=-centre + final_shift)[0]
                self.Gr.es[i]["pts"] = edge_position

            node_positions = base.shift(node_positions, _shift=final_shift)[0]
            for i in range(self.Gr.vcount()):
                self.Gr.vs[i]["o"] = node_positions[i]
                self.Gr.vs[i]["pts"] = node_positions[i]

        if weight_type is not None:
            self.Gr = base.add_weights(self, weight_type=weight_type, **kwargs)

        self.shape = list(
            max(list(self.Gr.vs[i]["o"][j] for i in range(self.Gr.vcount())))
            for j in (0, 1, 2)[0: self.dim]
        )

        if write:
            self.node_labelling([], [], write)

    def img_to_skel(
        self,
        name="skel.gsd",
        crop=None,
        skeleton=True,
        rotate=None,
        debubble=None,
        box=False,
        merge_nodes=None,
        prune=None,
        remove_objects=None,
    ):
        """Writes calculates and writes the skeleton to a :code:`.gsd` file.

        Note: if the rotation argument is given, this writes the union of all
        of the graph which can be obtained from cropping after rotation about
        the origin. The rotated skeleton can be written after the :attr:`graph`
        attribute has been set.

        Args:
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
        if not self._2d and rotate is not None:
            raise ValueError("Cannot rotate 3D graphs.")
        if crop is None and rotate is not None:
            raise ValueError("If rotating a graph, crop must be specified")
        if crop is not None and self.depth is not None:
            if crop[4] < self.depth[0] or crop[5] > self.depth[1]:
                raise ValueError(
                    "crop argument cannot be outwith the bounds of \
                    the network's depth"
                )
        if crop is not None and self.depth is None and not self._2d:
            if len(self.image_stack) < crop[5] - crop[4]:
                raise ValueError("Crop too large for image stack")
            else:
                self.depth = [crop[4], crop[5]]

        start = time.time()

        self.gsd_name = _abs_path(self, name)
        self.gsd_dir = os.path.split(self.gsd_name)[0]

        if rotate is not None:
            self.inner_cropper = _cropper(self, domain=crop)
            crop = self.inner_cropper._outer_crop

        self.set_img_bin(crop)

        if skeleton:
            self._skeleton = skeletonize(
                np.asarray(self._img_bin, dtype=np.dtype("uint8"))
            )
            self.skeleton_3d = skeletonize(
                np.asarray(self._img_bin_3d, dtype=np.dtype("uint8"))
            )
        else:
            self._img_bin = np.asarray(self._img_bin)
            self.skeleton_3d = self._img_bin_3d
            self._skeleton = self._img_bin

        positions = np.asarray(np.where(np.asarray(self.skeleton_3d) == 1)).T
        self.shape = np.asarray(
            list(max(positions.T[i]) + 1 for i in (2, 1, 0)[0: self.dim])
        )
        self.positions = positions

        with gsd.hoomd.open(name=self.gsd_name, mode="w") as f:
            s = gsd.hoomd.Frame()
            s.particles.N = len(positions)
            if box:
                L = list(max(positions.T[i]) for i in (0, 1, 2))
                s.particles.position, self.shift = base.shift(
                    positions, _shift=(L[0] / 2, L[1] / 2, L[2] / 2)
                )
                s.configuration.box = [L[0], L[1], L[2], 0, 0, 0]
            else:
                s.particles.position, self.shift = base.shift(positions)
            s.particles.types = ["A"]
            s.particles.typeid = ["0"] * s.particles.N
            f.append(s)

        end = time.time()
        print(
            "Ran img_to_skel() in ",
            end - start,
            "for skeleton with ",
            len(positions),
            "voxels",
        )

        if debubble is not None:
            self = base.debubble(self, debubble)

        if merge_nodes is not None:
            self = base.merge_nodes(self, merge_nodes)

        if prune is not None:
            self = base.prune(self, prune)

        if remove_objects is not None:
            self = base.remove_objects(self, remove_objects)

        # Until now, the rotation arguement has not been used; the image and
        # writted .gsds are all unrotated. The final block of this method is
        # for reassigning the image attribute, as well as setting the rotate
        # attribute for later. Only the img_bin attribute is altered because
        # the image_stack attribute exists to expose the unprocessed image to
        # the user.
        #
        # Also note that this only applies to 2D graphs, because 3D graphs
        # cannot be rotated.
        if rotate is not None:
            # Set the rotate attribute
            from scipy.spatial.transform import Rotation as R

            r = R.from_rotvec(rotate / 180 * np.pi * np.array([0, 0, 1]))
            self.rotate = r.as_matrix()
            self.crop = np.asarray(crop) - min(crop)
        else:
            self.rotate = None

    def node_labelling(self, attributes, labels, filename, edge_weight=None,
                       mode="w"):
        """Method saves a new :code:`.gsd` which labels the :attr:`graph`
        attribute with the given node attribute values. Method saves the
        :attr:`graph`  attribute in the :code:`.gsd` file in the form of a
        sparse adjacency matrix (therefore edge/node attributes are not saved).

        Args:
            attribute (:class:`numpy.ndarray`):
                An array of attribute values in ascending order of node id.
            label (str):
                The label to give the attribute in the file.
            filename (str):
                The file name to write.
            edge_weight (optional, :class:`numpy.ndarray`):
                Any edge weights to store in the adjacency matrix.
            mode (optional, str):
                The writing mode. See  for details.
        """
        if isinstance(self.Gr, list):
            self.Gr = self.Gr[0]

        if not isinstance(labels, list):
            labels = [
                labels,
            ]
            attributes = [
                attributes,
            ]

        if filename[0] == "/":
            save_name = filename
        else:
            save_name = self.stack_dir + "/" + filename
        if mode == "r+" and os.path.exists(save_name):
            _mode = "r+"
        else:
            _mode = "w"

        f = gsd.hoomd.open(name=save_name, mode=_mode)
        self.labelled_name = save_name

        centroid_positions = np.empty((0, self.dim))
        node_positions = np.empty((0, self.dim))
        edge_positions = np.empty((0, self.dim))
        for i in range(len(self.Gr.vs())):
            node_positions = np.vstack((node_positions,
                                        self.Gr.vs()[i]["pts"]))
            centroid_positions = np.vstack((centroid_positions,
                                            self.Gr.vs()[i]["o"]))
        for i in range(len(self.Gr.es())):
            edge_positions = np.vstack((edge_positions,
                                        self.Gr.es()[i]["pts"]))

        if self._2d:
            node_positions = np.hstack(
                (np.zeros((len(node_positions), 1)), node_positions)
            )
            edge_positions = np.hstack(
                (np.zeros((len(edge_positions), 1)), edge_positions)
            )
            centroid_positions = np.hstack(
                (np.zeros((len(centroid_positions), 1)), centroid_positions)
            )

        positions = np.vstack((edge_positions,
                               node_positions,
                               centroid_positions))

        self.positions = positions

        L = list(max(positions.T[i]) * 2 for i in (0, 1, 2))
        node_positions = base.shift(
            node_positions, _shift=(L[0] / 4, L[1] / 4, L[2] / 4)
        )[0]
        edge_positions = base.shift(
            edge_positions, _shift=(L[0] / 4, L[1] / 4, L[2] / 4)
        )[0]
        centroid_positions = base.shift(
            centroid_positions, _shift=(L[0] / 4, L[1] / 4, L[2] / 4)
        )[0]
        positions = base.shift(positions,
                               _shift=(L[0] / 4, L[1] / 4, L[2] / 4))[0]

        s = gsd.hoomd.Frame()
        N = len(positions)
        s.particles.N = N
        s.particles.position = positions
        s.particles.types = ["Edge", "Node", "Centroid"]
        # s.particles.typeid = [0] * N
        s.particles.typeid = np.array(
            [
                0,
            ]
            * len(edge_positions)
            + [
                1,
            ]
            * len(node_positions)
            + [
                2,
            ]
            * len(centroid_positions)
        )
        s.configuration.box = [L[0] / 2, L[1] / 2, L[2] / 2, 0, 0, 0]
        for label in labels:
            s.log["particles/" + label] = [np.NaN] * N

        # Store adjacency matrix in CSR format
        matrix = self.Gr.get_adjacency_sparse(attribute=edge_weight)
        rows, columns = matrix.nonzero()
        values = matrix.data

        s.log["Adj_rows"] = rows
        s.log["Adj_cols"] = columns
        s.log["Adj_values"] = values
        s.log["Edge_lens"] = list(map(lambda edge: len(edge),
                                      self.Gr.es["pts"]))
        s.log["Node_lens"] = list(map(lambda node: len(node),
                                      self.Gr.vs["pts"]))

        for i in range(len(centroid_positions)):
            for attribute, label in zip(attributes, labels):
                s.log["particles/" + label][
                    len(node_positions) + len(edge_positions) + i
                ] = attribute[i]

        f.append(s)

        _dict = {}
        for attr in ("stack_dir", "_2d", "dim", "cropper"):
            _dict[attr] = str(getattr(self, attr))

        name = os.path.splitext(os.path.basename(filename))[0]
        with open(self.stack_dir + "/" + name + ".json", "w") as json_file:
            json.dump(_dict, json_file)

    def node_plot(self, parameter=None, ax=None, depth=0):
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
            parameter = np.ones(self.Gr.vcount(), dtype=np.intc)
            _parameter = False

        assert self.Gr.vcount() == len(parameter)

        if ax is None:
            fig = plt.figure()
            ax = fig.subplots()

        ax.set_xticks([])
        ax.set_yticks([])
        ax.imshow(self.image_stack[depth][0][self.cropper._2d], cmap="gray")

        e = np.empty((0, 2))
        for edge in self.graph.es:
            e = np.vstack((e, edge["pts"]))
        ax.scatter(e.T[1], e.T[0], c="k", s=3, marker="s", edgecolors="none")

        y, x = np.array(self.graph.vs["o"]).T
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
            cb = colorbar(sp)
            cb.set_label("Value")

        return ax

    def edge_plot(
        self,
        parameter=None,
        ax=None,
        depth=0,
        edge_cmap="plasma",
        plot_img=True,
        **kwargs,
    ):
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
            ax.imshow(self.image_stack[depth][0][self.cropper._2d],
                      cmap="gray")
        _max = np.max(parameter)
        _min = np.min(parameter)

        for param, edge in zip(parameter, self.graph.es):
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

        y, x = np.array(self.graph.vs["o"]).T
        ax.scatter(x, y, s=10, marker="o", edgecolors="none", c="red")

        norm = mpl.colors.Normalize(vmin=_min, vmax=_max)
        mappable = mpl.cm.ScalarMappable(norm=norm, cmap=edge_cmap)
        if _parameter:
            cb = colorbar(mappable, ax)
            cb.set_label("Value")

        return fig, ax

    def graph_plot(self, ax=None, depth=0):
        """Superimpose the graph and original image.

        Args:
            ax (:class:`matplotlib.axes.Axes`, optional):
                Axis to plot on. If :code:`None`, make a new figure and axis.
                (Default value = :code:`None`)

            depth (int, optional): If the network is 3D, which slice to plot.

        Returns:
            (:class:`matplotlib.axes.Axes`): Axis with the plot.
        """

        return self.node_plot(ax=ax, depth=depth)

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

    @property
    def img_bin(self):
        """:class:`np.ndarray`: The binary image from which the graph was
        extracted"""
        return self._img_bin

    @img_bin.setter
    def img_bin(self, value):
        warnings.warn(
            "Setting the binary image should not be necessary if \
                      the raw data has been binarized."
        )

    @property
    def graph(self):
        """:class:`igraph.Graph`: The Graph object extracted from the
        skeleton"""
        return self.Gr

    @property
    def image(self):
        """:class:`np.ndarray`: The original image used to obtain the graph."""
        if self._2d:
            return self.image_stack[0][0]
        else:
            return self.image_stack[:][0]

    @property
    def skeleton(self):
        """:class:`np.ndarray`: The original skeleton."""
        return self._skeleton

    @classmethod
    def from_gsd(cls, filename, frame=0, depth=None, dim=2):
        """
        Alternative constructor for returning a Network object that was
        previously stored in a `.gsd` and `.json` file. Assumes file is stored
        in the same directory as *StructuralGT* wrote it to. I.e. assumed name
        given as `.../dir/Binarized/name.gsd`.
        """

        assert os.path.exists(filename)
        _dir = os.path.abspath(filename)
        _dir = os.path.split(os.path.split(filename)[0])[0]
        binarized_dir = os.path.split(os.path.split(filename)[0])[-1]
        N = cls(_dir, depth=depth, dim=dim, binarized_dir=binarized_dir)
        if dim == 2:
            N._2d = True
        else:
            N._2d = False

        name = os.path.splitext(os.path.basename(filename))[0]
        _json = N.stack_dir + "/" + name + ".json"
        with open(_json) as json_file:
            data = json.load(json_file)

        N.cropper = _cropper.from_string(N, domain=data["cropper"])
        N._2d = bool(data["cropper"])
        N.dim = int(data["dim"])
        f = gsd.hoomd.open(name=filename, mode="r")[frame]
        rows = f.log["Adj_rows"]
        cols = f.log["Adj_cols"]
        values = f.log["Adj_values"]
        S = scipy.sparse.csr_matrix((values, (rows, cols)))
        G = ig.Graph()
        N.Gr = G.Weighted_Adjacency(S, mode="upper")

        first_axis = {2: 1, 3: 0}[N.dim]
        edge_pos = f.particles.position[f.particles.typeid == 0].T[
                first_axis:3].T
        node_pos = f.particles.position[f.particles.typeid == 1].T[
                first_axis:3].T
        centroid_pos = f.particles.position[f.particles.typeid == 2].T[
                first_axis:3].T

        N.Gr.es["pts"] = base.split(
            base.shift(edge_pos, _2d=N._2d)[0].astype(int), f.log["Edge_lens"]
        )
        N.Gr.vs["pts"] = base.split(
            base.shift(node_pos, _2d=N._2d)[0].astype(int), f.log["Node_lens"]
        )
        N.Gr.vs["o"] = base.shift(centroid_pos, _2d=N._2d)[0].astype(int)

        return N


def Graph(filename, frame=0):
    """Functions which returns an `igraph.Graph` object from a gsd, with
    node and edge position attributes. Useful when a `Network` object is not
    required. Unlike `Network.from_gsd`, it makes no assumptions about the
    path of the `gsd` file.

    Args:
        filename (str):
            The file name to read.

    Returns:
        (`igraph.Graph`): igraph Graph object.
    """

    f = gsd.hoomd.open(name=filename, mode="r")[frame]
    rows = f.log["Adj_rows"]
    cols = f.log["Adj_cols"]
    values = f.log["Adj_values"]
    S = scipy.sparse.csr_matrix((values, (rows, cols)))
    Gr = ig.Graph.Weighted_Adjacency(S, mode="upper")

    edge_pos = f.particles.position[f.particles.typeid == 0]
    node_pos = f.particles.position[f.particles.typeid == 1]
    centroid_pos = f.particles.position[f.particles.typeid == 2]

    Gr.es["pts"] = edge_pos
    Gr.vs["pts"] = node_pos
    Gr.vs["o"] = centroid_pos

    return Gr


class Regions:
    def __init__(self, partition, box):
        if partition == 0:
            self.regions = [
                [
                    (-box[0] / 2, box[0] / 2),
                    (-box[1] / 2, box[1] / 2),
                    (-box[2] / 2, box[2] / 2),
                ]
            ]
        elif partition == 1:
            self.regions = [
                [(-box[0] / 2, 0), (-box[1] / 2, 0), (-box[2] / 2, 0)],
                [(-box[0] / 2, 0), (-box[1] / 2, 0), (0, box[2] / 2)],
                [(-box[0] / 2, 0), (0, box[1] / 2), (-box[2] / 2, 0)],
                [(-box[0] / 2, 0), (0, box[1] / 2), (0, box[2] / 2)],
                [(0, box[0] / 2), (-box[1] / 2, 0), (-box[2] / 2, 0)],
                [(0, box[0] / 2), (-box[1] / 2, 0), (0, box[2] / 2)],
                [(0, box[0] / 2), (0, box[1] / 2), (-box[2] / 2, 0)],
                [(0, box[0] / 2), (0, box[1] / 2), (0, box[2] / 2)],
            ]

    def inregion(self, region, p):
        mask = (
            np.array(p.T[0] > region[0][0])
            & np.array(p.T[0] < region[0][1])
            & np.array(p.T[1] > region[1][0])
            & np.array(p.T[1] < region[1][1])
            & np.array(p.T[2] > region[2][0])
            & np.array(p.T[2] < region[2][1])
        )

        return p[mask]


class ParticleNetwork(Sequence):
    def __init__(self, trajectory, cutoff, partition=0, periodic=False):
        self.traj = gsd.hoomd.open(trajectory)
        self.cutoff = cutoff
        self.periodic = periodic
        self.partition = partition

        self.regions = Regions(partition, self.traj[0].configuration.box)

    def __getitem__(self, key):
        self._graph_list = []
        if isinstance(key, int):
            _iter = [self.traj[key]]
        else:
            _iter = self.traj[key]
        for frame in _iter:
            _first = True
            for region in self.regions.regions:
                positions = self.regions.inregion(region,
                                                  frame.particles.position)
                box = frame.configuration.box * {False: 2, True: 1}[
                        self.periodic]
                aq = freud.locality.AABBQuery(box, positions)
                nlist = aq.query(
                    positions,
                    {"r_max": self.cutoff, "exclude_ii": True},
                ).toNeighborList()
                nlist.filter(nlist.query_point_indices < nlist.point_indices)
                if _first:
                    _graph = ig.Graph.TupleList(nlist[:], directed=False)
                    _first = False
                else:
                    nlist = nlist[:] + _graph.vcount()
                    __graph = ig.Graph.TupleList(nlist[:], directed=False)
                    _graph = ig.operators.union([_graph, __graph])

            self._graph_list.append(_graph)

        return self._graph_list

    def __len__(self):
        return len(self._graph_list)


class PointNetwork:
    """Class for creating graphs from point cloud data.

    Args:
        positions (:class:`numpy.ndarray`):
            The coordinates of the points in the point cloud.
        cutoff (float):
            The cutoff distance for creating edges between points.
        periodic (bool):
            Whether to use periodic boundary conditions. Default is False.
    """

    def __init__(self, positions, cutoff, periodic=False):
        self.cutoff = cutoff
        self.periodic = periodic
        self.dim = positions.shape[1]

        for dim in range(self.dim):
            positions[:, dim] = (positions[:, dim] - positions[:, dim].min())
        L = list(max(positions.T[i]) for i in range(self.dim))
        positions, _ = base.shift(positions,
                                  _shift=(L[0] / 2, L[1] / 2, L[2] / 2))
        box = [L[0], L[1], L[2], 0, 0, 0]

        self.positions = positions
        self.box = box

        aq = freud.locality.AABBQuery(self.box, positions)
        nlist = aq.query(
            positions,
            {"r_max": self.cutoff, "exclude_ii": True},
        ).toNeighborList()
        nlist.filter(nlist.query_point_indices < nlist.point_indices)
        self.graph = ig.Graph()
        self.graph.add_vertices(len(positions))
        # Create edges based on the neighbor list
        for i in range(len(nlist.point_indices)):
            self.graph.add_edge(
                nlist.point_indices[i],
                nlist.query_point_indices[i],
            )

    def point_to_skel(self, filename='skel.gsd'):
        """Method saves a new :code:`.gsd` with the graph
        structure.

        Args:
            filename (str):
               The filename to save the :code:`.gsd` file to.
        """

        N = self.graph.vcount()
        bonds = np.array(self.graph.get_edgelist())
        bond_types = ['0']

        snapshot = gsd.hoomd.Frame()
        snapshot.particles.N = N
        snapshot.particles.types = ['A']
        snapshot.particles.position = self.positions
        snapshot.particles.typeid = [0] * N
        snapshot.particles.bond_types = bond_types
        snapshot.particles.bonds = bonds
        snapshot.configuration.box = self.box
        snapshot.bonds.N = len(bonds)
        snapshot.bonds.group = bonds
        snapshot.bonds.types = bond_types
        snapshot.bonds.typeid = np.zeros(len(bonds), dtype=np.uint32)

        with gsd.hoomd.open(name=filename, mode='w') as f:
            f.append(snapshot)

        self.filename = filename

    def node_labelling(self, attributes, labels, filename='labelled.gsd'):
        """Method saves a new :code:`.gsd` which labels the :attr:`graph`
        attribute with the given node attribute values.

        Args:
            attribute (:class:`numpy.ndarray`):
                An array of attribute values in ascending order of node id.
            label (str):
                The label to give the attribute in the file.
        """

        if not isinstance(labels, list):
            labels = [labels,]
            attributes = [attributes,]

        with gsd.hoomd.open(name=self.filename, mode='r') as f:
            s = f[0]
            for attribute, label in zip(attributes, labels):
                if len(attribute) != s.particles.N:
                    raise ValueError(
                            f"Attribute length {len(attribute)} "
                            "does not match number of particles "
                            "{s.particles.N}."
                            )
                s.log["particles/" + label] = attribute

        with gsd.hoomd.open(name=filename, mode='w') as f_mod:
            f_mod.append(s)
