# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import numpy as np


def unitvector(u, v):
    # Inputs:
    # u, v: two coordinates (x, y) or (x, y, z)

    vec = u - v  # find the vector between u and v

    if np.linalg.norm(vec) == 0:
        return np.array(
            [
                0,
            ]
            * len(u),
            dtype=np.float16,
        )
    else:
        return vec / np.linalg.norm(vec)


def halflength(u, v):
    # Inputs:
    # u, v: two coordinates (x, y) or (x, y, z)

    vec = u - v  # find the vector between u and v

    # returns half of the length of the vector
    return np.linalg.norm(vec) / 2


def findorthogonal(u, v):
    # Inputs:
    # u, v: two coordinates (x, y) or (x, y, z)

    n = unitvector(u, v)  # make n a unit vector along u,v
    # if (np.isnan(n[0]) or np.isnan(n[1])):
    #    n[0] , n[1] = float(0) , float(0)
    hl = halflength(u, v)  # find the half-length of the vector u,v
    orth = np.random.randn(len(u))  # take a random vector
    orth -= orth.dot(n) * n  # make it orthogonal to vector u,v
    orth /= np.linalg.norm(orth)  # make it a unit vector

    # Returns the coordinates of the midpoint of vector u,v; the orthogonal
    # unit vector
    return (v + n * hl), orth


def boundarycheck(coord, w, h, d=None):
    # Inputs:
    # coord: the coordinate (x,y) to check; no (x,y,z) compatibility yet
    # w,h: the width and height of the image to set the boundaries
    _2d = len(coord) == 2
    oob = 0  # Generate a boolean check for out-of-boundary
    # Check if coordinate is within the boundary
    if _2d:
        if (coord[0] < 0 or coord[1] < 0
                or coord[0] > (w - 1) or coord[1] > (h - 1)):
            oob = 1
            coord = np.array([1, 1])
    else:
        if sum(coord < 0) > 0 or sum(coord > [w - 1, h - 1, d - 1]) > 0:
            oob = 1
            coord = np.array([1, 1, 1])

    # returns the boolean oob (1 if boundary error)
    # coordinates (reset to (1,1) if boundary error)
    return oob, coord.astype(int)


def lengthtoedge(m, orth, img_bin):
    # Inputs:
    # m: the midpoint of a trace of an edge
    # orth: an orthogonal unit vector
    # img_bin: the binary image that the graph is derived from

    _2d = len(m) == 2
    if _2d:
        w, h = img_bin.shape  # finds dimensions of img_bin for boundary check
    else:
        w, h, d = img_bin.shape

    check = 0  # initializing boolean check
    i = 0  # initializing iterative variable
    while (
        check == 0
    ):  # iteratively check along orthogonal vector to see if the coordinate
        # is either...
        ptcheck = (
            m + i * orth
        )  # ... out of bounds, or no longer within the fiber in img_bin
        ptcheck = ptcheck.astype(int)
        if _2d:
            oob, ptcheck = boundarycheck(ptcheck, w, h)
            Q_edge = (
                img_bin[ptcheck[0], ptcheck[1]] == 0 or oob == 1
            )  # Checks if point in fibre
        else:
            oob, ptcheck = boundarycheck(ptcheck, w, h, d=d)
            Q_edge = (img_bin[ptcheck[0], ptcheck[1],
                              ptcheck[2]] == 0 or oob == 1)
        if Q_edge:
            edge = m + (i - 1) * orth
            edge = edge.astype(int)
            # When the check indicates oob or black space, assign width to l1
            l1 = edge
            check = 1
        else:
            i += 1

    check = 0
    i = 0
    while check == 0:  # Repeat, but following the negative orthogonal vector
        ptcheck = m - i * orth
        ptcheck = ptcheck.astype(int)
        if _2d:
            oob, ptcheck = boundarycheck(ptcheck, w, h)
            Q_edge = (
                img_bin[ptcheck[0], ptcheck[1]] == 0 or oob == 1
            )  # Checks if point in fibre
        else:
            oob, ptcheck = boundarycheck(ptcheck, w, h, d=d)
            Q_edge = (img_bin[ptcheck[0], ptcheck[1],
                              ptcheck[2]] == 0 or oob == 1)
        if Q_edge:
            edge = m - (i - 1) * orth
            edge = edge.astype(int)
            # When the check indicates oob or black space, assign width to l1
            l2 = edge
            check = 1
        else:
            i += 1

    # returns the length between l1 and l2, which is the width of the fiber
    # associated with an edge, at its midpoint
    return l1, l2


# Note that when pixel widths or lengths are 0, the following function assigns
# unity edge weight, which is arbitrary. We do not assign 0 because this
# would cause extra 0 elements on the Laplacian, which would render linear
# transport flow problems underdetermined.
def assignweights(ge, img_bin, weight_type=None, R_j=0, rho_dim=1):

    if len(ge) < 2:
        pix_width = 10
        wt = 1
    # if ge exists, find the midpoint of the trace, and orthogonal unit vector
    else:
        endindex = len(ge) - 1
        midindex = int(len(ge) / 2)
        pt1 = ge[0]
        pt2 = ge[endindex]
        m = ge[midindex]
        midpt, orth = findorthogonal(pt1, pt2)
        m.astype(int)
        l1, l2 = lengthtoedge(m, orth, img_bin)
        pix_width = int(np.linalg.norm(l1 - l2))
        length = len(ge)
    if weight_type is None:
        wt = pix_width / 10
    elif weight_type == "VariableWidthConductance":
        # This is electrical conductance; not graph conductance.
        # This conductance is based on both width and length of edge,
        # as measured from the raw data. rho_dim is resistivity
        # (i.e. ohm pixels)
        if pix_width == 0 or length == 0:
            wt = 1
        else:
            wt = ((length * rho_dim / pix_width**2) + R_j * 2) ** -1
    elif weight_type == "FixedWidthConductance":
        # This conductance is based on length of edge, as measured from data
        # whereas width is supplied as part of rho_dim.
        # rho_dim should be equal resistivity/cross_secitonal area
        length = len(ge)
        if pix_width == 0 or length == 0:
            wt = 1
        else:
            wt = ((length * rho_dim) + R_j * 2) ** -1
    elif weight_type == "Resistance":  # Reciprocal of conductance
        length = len(ge)
        if pix_width == 0 or length == 0:
            wt = 1
        else:
            wt = (length * rho_dim / pix_width**2) + R_j * 2
    elif weight_type == "Area":
        if pix_width == 0 or length == 0:
            wt = 1
        else:
            wt = pix_width**2
    elif weight_type == "Width":
        if pix_width == 0 or length == 0:
            wt = 1
        else:
            wt = pix_width
    elif weight_type == "Length":
        wt = len(ge)
    elif weight_type == "InverseLength":
        wt = len(ge) ** -1
    elif weight_type == "PerpBisector":
        wt = np.array([l1, l2])
    else:
        raise TypeError("Invalid weight type")

    # returns the width in pixels; the weight which
    return pix_width, wt
