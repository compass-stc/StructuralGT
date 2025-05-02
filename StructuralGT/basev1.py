# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import os
import time

import cv2 as cv
import gsd.hoomd
import numpy as np
from skimage.morphology import (binary_closing, remove_small_objects,
                                skeletonize)

from StructuralGT import GetWeights_3d, error, skel_ID, sknwEdits


def read(name, read_type):
    """For raising an error when a file does not exist because cv.imread does
    not do this.
    """
    out = cv.imread(name, read_type)
    if out is None:
        raise ValueError(name + " does not exist")
    else:
        return out


def Q_img(name):
    """Returns True if name is a supported image file type.

    Args:
        name (str):
            Name of file.

    Returns:
        bool: Whether the extension type is a supported image file.
    """
    if (
        name.endswith(".tiff")
        or name.endswith(".tif")
        or name.endswith(".jpg")
        or name.endswith(".jpeg")
        or name.endswith(".png")
        or name.endswith(".bmp")
        or name.endswith(".gif")
    ):
        return True
    else:
        return False


def connector(point1, point2):
    """For 2 points on a lattice, this function returns the lattice points
    which join them

    Args:
        point1 (list[int]):
            Coordinates of the first point.
        point2 (list[int]):
            Coordinates of the second point.

    Returns:
        :class:`numpy.ndarray`: Array of lattice points connecting point1
        and point2
    """
    vec = point2 - point1
    edge = np.array([point1])
    for i in np.linspace(0, 1):
        edge = np.append(edge,
                         np.array([point1 + np.multiply(i, vec)]), axis=0)
    edge = edge.astype(int)
    edge = np.unique(edge, axis=0)

    return edge


def split(array, splitpoints):
    """Function which splits numpy array into list of arrays, according to
    the split points specified in splitpoints (which is a list of the array
    lengths."""
    splitpoints = np.pad(splitpoints, (1, 1), "constant",
                         constant_values=(0, 0))
    L = []
    k = 0
    for i, j in zip(splitpoints[0: len(splitpoints)], splitpoints[1::]):
        L.append(array[i + k: i + j + k])
        k += i

    return L


def shift(points, _2d=False, _shift=None):
    """Translates all points such that the minimum coordinate in points is
    the origin.

    Args:
        points (:class:`numpy.ndarray`):
            The points to shift.
        _2d (bool):
            Whether the points are 2D coordinates.
        _shift (:class:`numpy.ndarray`):
            The shift to apply

    Returns:
        :class:`numpy.ndarray`: The shifted points.
        :class:`numpy.ndarray`: The applied shift.
    """
    if _shift is None:
        if _2d:
            _shift = np.full(
                (np.shape(points)[0], 2),
                [np.min(points.T[0]), np.min(points.T[1])],
            )
        else:
            _shift = np.full(
                (np.shape(points)[0], 3),
                [
                    np.min(points.T[0]),
                    np.min(points.T[1]),
                    np.min(points.T[2]),
                ],
            )

    points = points - _shift

    return points, _shift


def oshift(points, _2d=False, _shift=None):
    """Translates all points such that the points become approximately centred
    at the origin.

    Args:
        points (:class:`numpy.ndarray`):
            The points to shift.
        _2d (bool):
            Whether the points are 2D coordinates.
        _shift (:class:`numpy.ndarray`):
            The shift to apply.

    Returns:
        :class:`numpy.ndarray`: The shifted points.
        :class:`numpy.ndarray`: The applied shift.
    """
    if _shift is None:
        if _2d:
            _shift = np.full(
                (np.shape(points)[0], 2),
                [np.max(points.T[0]) / 2, np.max(points.T[1]) / 2],
            )
            _shift = np.full(
                (np.shape(points)[0], 3),
                [
                    np.max(points.T[0]) / 2,
                    np.max(points.T[1]) / 2,
                    np.max(points.T[2]) / 2,
                ],
            )

    points = points - _shift

    return points


def isinside(points, crop):
    """Determines whether the given points are all within the given crop.

    Args:
        points (:class:`numpy.ndarray`):
            The points to check.
        crop (list):
            The x, y, and (optionally) z coordinates of the space to check
            for membership.

    Returns:
        bool: Whether all the points are within the crop region.
    """

    if points.T.shape[0] == 2:
        for point in points:
            if (
                point[0] < crop[0]
                or point[0] > crop[1]
                or point[1] < crop[2]
                or point[1] > crop[3]
            ):
                return False
            return True
    else:
        for point in points:
            if (
                point[0] < crop[0]
                or point[0] > crop[1]
                or point[1] < crop[2]
                or point[1] > crop[3]
                or point[2] < crop[4]
                or point[2] > crop[5]
            ):
                return False
            return True


def dim_red(positions):
    """For lists of positions where all elements along one axis have the same
    value, this returns the same list of positions but with the redundant
    dimension(s) removed.

    Args:
        positions (:class:`numpy.ndarray`):
            The positions to reduce.

    Returns:
        :class:`numpy.ndarray`: The reduced positions
    """

    unique_positions = np.asarray(
        list(len(np.unique(positions.T[i])) for i in range(len(positions.T)))
    )
    redundant = unique_positions == 1
    positions = positions.T[~redundant].T

    return positions


def G_to_gsd(G, gsd_name, box=False):
    """Remove?"""
    dim = len(G.vs[0]["o"])

    positions = np.asarray(list(G.vs[i]["o"] for i in range(G.vcount())))
    for i in range(G.ecount()):
        positions = np.append(positions, G.es[i]["pts"], axis=0)

    N = len(positions)
    if dim == 2:
        positions = np.append([np.zeros(N)], positions.T, axis=0).T

    s = gsd.hoomd.Frame()
    s.particles.N = N
    s.particles.types = ["A"]
    s.particles.typeid = ["0"] * N

    if box:
        L = list(max(positions.T[i]) for i in (0, 1, 2))
        s.particles.position, _ = shift(
            positions, _shift=(L[0] / 2, L[1] / 2, L[2] / 2)
        )
        s.configuration.box = [L[0], L[1], L[2], 0, 0, 0]
    else:
        s.particles.position, _ = shift(positions)

    with gsd.hoomd.open(name=gsd_name, mode="w") as f:
        f.append(s)


def gsd_to_G(gsd_name, sub=False, _2d=False, crop=None):
    """Function takes gsd rendering of a skeleton and returns the list of
    nodes and edges, as calculated by sknw.

    Args:
        gsd_name (str):
            The file name to write.
        sub (optional, bool):
            Whether to return only to largest connected component. If True, it
            will reduce the returned graph to the largest connected induced
            subgraph, resetting node numbers to consecutive integers,
            starting from 0.
        _2d (optional, bool):
            Whether the skeleton is 2D. If True it only ensures additional
            redundant axes from the position array is removed. It does not
            guarantee a 3d graph.
        crop (list):
            The x, y and (optionally) z coordinates of the cuboid/shape
            enclosing the skeleton from which a :class:`igraph.Graph` object
            should be extracted.

    Returns:
        (:class:`igraph.Graph`): The extracted :class:`igraph.Graph` object.
    """
    frame = gsd.hoomd.open(name=gsd_name, mode="r")[0]
    positions = shift(frame.particles.position.astype(int))[0]
    if crop is not None:
        from numpy import logical_and as a

        p = positions.T
        positions = p.T[
            a(
                a(a(p[1] >= crop[0], p[1] <= crop[1]), p[2] >= crop[2]),
                p[2] <= crop[3],
            )
        ]
        positions = shift(positions)[0]

    if sum((positions < 0).ravel()) != 0:
        positions = shift(positions)[0]

    if _2d:
        positions = dim_red(positions)
        new_pos = np.zeros(positions.T.shape)
        new_pos[0] = positions.T[0]
        new_pos[1] = positions.T[1]
        positions = new_pos.T.astype(int)

    canvas = np.zeros(
        list((max(positions.T[i]) + 1) for i in list(
            range(min(positions.shape))))
    )
    canvas[tuple(list(positions.T))] = 1
    canvas = canvas.astype(int)

    G = sknwEdits.build_sknw(canvas)

    if sub:
        G = sub_G(G)

    return G


def sub_G(G):
    """Function generates largest connected induced subgraph. Node and edge
    numbers are reset such that they are consecutive integers, starting
    from 0."""

    print(f"Before removing smaller components, graph has {G.vcount()}  nodes")
    components = G.connected_components()
    G = components.giant()
    print(f"After removing smaller components, graph has {G.vcount()}  nodes")

    # G_sub  = G.subgraph(max(nx.connected_components(G), key=len).copy())
    # G = nx.relabel.convert_node_labels_to_integers(G_sub)

    return G


def debubble(g, elements):
    if not isinstance(elements, list):
        raise error.StructuralElementError

    start = time.time()
    g.gsd_name = g.gsd_dir + "/debubbled_" + os.path.split(g.gsd_name)[1]

    canvas = g.img_bin
    for elem in elements:
        canvas = skeletonize(canvas) / 255
        canvas = binary_closing(canvas, footprint=elem)

    g._skeleton = skeletonize(canvas) / 255

    if g._2d:
        g._skeleton_3d = np.swapaxes(np.array([g._skeleton]), 2, 1)
        g._skeleton_3d = np.asarray([g._skeleton])
    else:
        g._skeleton_3d = np.asarray(g._skeleton)

    positions = np.asarray(np.where(g._skeleton_3d != 0)).T
    with gsd.hoomd.open(name=g.gsd_name, mode="w") as f:
        s = gsd.hoomd.Frame()
        s.particles.N = int(sum(g._skeleton_3d.ravel()))
        s.particles.position = positions
        s.particles.types = ["A"]
        s.particles.typeid = ["0"] * s.particles.N
        f.append(s)
    end = time.time()
    print(
        f"Ran debubble in {end - start} for an image with shape \
        {g._skeleton_3d.shape}"
    )

    return g


# Currently works for 2D only (Is just a reproduction of Drew's method)
def merge_nodes(g, disk_size):
    start = time.time()
    g.gsd_name = g.gsd_dir + "/merged_" + os.path.split(g.gsd_name)[1]

    canvas = g._skeleton
    g._skeleton = skel_ID.merge_nodes(canvas, disk_size)

    if g._2d:
        g._skeleton_3d = np.swapaxes(np.array([g._skeleton]), 2, 1)
        g._skeleton_3d = np.asarray([g._skeleton])
    else:
        g._skeleton_3d = np.asarray(g._skeleton)

    positions = np.asarray(np.where(g._skeleton_3d != 0)).T
    with gsd.hoomd.open(name=g.gsd_name, mode="w") as f:
        s = gsd.hoomd.Frame()
        s.particles.N = int(sum(g._skeleton_3d.ravel()))
        s.particles.position = positions
        s.particles.types = ["A"]
        s.particles.typeid = ["0"] * s.particles.N
        f.append(s)
    end = time.time()
    print(
        f"Ran merge in {end - start} for an image with shape \
        {g._skeleton_3d.shape}"
    )

    return g


def prune(g, size):
    start = time.time()
    g.gsd_name = g.gsd_dir + "/pruned_" + os.path.split(g.gsd_name)[1]

    canvas = g._skeleton
    g._skeleton = skel_ID.pruning(canvas, size)

    if g._2d:
        g._skeleton_3d = np.swapaxes(np.array([g._skeleton]), 2, 1)
        g._skeleton_3d = np.asarray([g._skeleton])
    else:
        g._skeleton_3d = np.asarray(g._skeleton)

    positions = np.asarray(np.where(g._skeleton_3d != 0)).T
    with gsd.hoomd.open(name=g.gsd_name, mode="w") as f:
        s = gsd.hoomd.Frame()
        s.particles.N = int(sum(g._skeleton_3d.ravel()))
        s.particles.position = positions
        s.particles.types = ["A"]
        s.particles.typeid = ["0"] * s.particles.N
        f.append(s)
    end = time.time()
    print(
        f"Ran prune in {end - start} for an image with shape \
        {g._skeleton_3d.shape}"
    )

    return g


def remove_objects(g, size):
    start = time.time()
    g.gsd_name = g.gsd_dir + "/cleaned_" + os.path.split(g.gsd_name)[1]

    canvas = g._skeleton
    g._skeleton = remove_small_objects(canvas, size, connectivity=2)

    if g._2d:
        g._skeleton_3d = np.swapaxes(np.array([g._skeleton]), 2, 1)
        g._skeleton_3d = np.asarray([g._skeleton])
    else:
        g._skeleton_3d = np.asarray(g._skeleton)

    positions = np.asarray(np.where(g._skeleton_3d != 0)).T
    with gsd.hoomd.open(name=g.gsd_name, mode="w") as f:
        s = gsd.hoomd.Frame()
        s.particles.N = int(sum(g._skeleton_3d.ravel()))
        s.particles.position = positions
        s.particles.types = ["A"]
        s.particles.typeid = ["0"] * s.particles.N
        f.append(s)
    end = time.time()
    print(
        f"Ran remove objects in {end - start} for an image with shape \
        {g._skeleton_3d.shape}"
    )

    return g


def add_weights(g, weight_type=None, R_j=0, rho_dim=1):
    _img_bin = g.img_bin[g.shift[0][1]::, g.shift[0][2]::]
    if not isinstance(weight_type, list) and weight_type is not None:
        raise TypeError("weight_type must be list, even if single element")
    for _type in weight_type:
        for i, edge in enumerate(g.Gr.es()):
            ge = edge["pts"]
            pix_width, wt = GetWeights_3d.assignweights(
                ge, _img_bin, weight_type=_type, R_j=R_j, rho_dim=rho_dim
            )
            edge["pixel width"] = pix_width
            if (_type == "VariableWidthConductance"
                    or _type == "FixedWidthConductance"):
                _type_name = "Conductance"
            else:
                _type_name = _type
            edge[_type_name] = wt

    return g.Gr


def quadrupletise(i):
    if len(str(i)) == 4:
        return str(i)
    elif len(str(i)) == 3:
        return "0" + str(i)
    elif len(str(i)) == 2:
        return "00" + str(i)
    elif len(str(i)) == 1:
        return "000" + str(i)
    else:
        raise ValueError


# 1-2-3 and 3-2-1 not double counted
# but 1-2-3 and 1-3-2 are double counted
def loops(Gr, n):
    A = np.array(Gr.get_adjacency().data, dtype=np.single)
    for _ in range(n):
        A = np.power(A, A)

    return np.trace(A) / 2
