# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import numpy as np
import gsd.hoomd


# USED IN "ROTATE"?
def shift(points, _2d=False, _shift=None):
    """
    Translates all points such that the minimum coordinate in points is the origin.

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


# USED IN "ROTATE"?
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


# USED IN "ROTATE"?
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