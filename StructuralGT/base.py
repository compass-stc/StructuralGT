# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import numpy as np


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
