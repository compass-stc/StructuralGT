"""GetWeights: Obtains the 'weight' of fibers in a binary
image by measuring the pixel width of the perpendicular bisector.

Copyright (C) 2021, The Regents of the University of Michigan.

This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

Contributers: Drew Vecchio, Samuel Mahler, Mark D. Hammig, Nicholas A. Kotov
Contact email: vecdrew@umich.edu
"""

import numpy as np

def unitvector(u,v):
    # Inputs:
    # u, v: two coordinates (x, y) or (x, y, z)

    vec = u-v # find the vector between u and v

    # returns the unit vector in the direction from v to u
    return vec/np.linalg.norm(vec)

def halflength(u,v):
    # Inputs:
    # u, v: two coordinates (x, y) or (x, y, z)

    vec = u-v # find the vector between u and v

    # returns half of the length of the vector
    return np.linalg.norm(vec)/2

def findorthogonal(u,v):
    # Inputs:
    # u, v: two coordinates (x, y) or (x, y, z)

    n = unitvector(u,v)         # make n a unit vector along u,v
    if (np.isnan(n[0]) or np.isnan(n[1])):
        n[0] , n[1] = float(0) , float(0)
    hl = halflength(u,v)        # find the half-length of the vector u,v
    orth = np.random.randn(len(u))   # take a random vector
    orth -= orth.dot(n) * n     # make it orthogonal to vector u,v
    orth /= np.linalg.norm(orth)# make it a unit vector

    # Returns the coordinates of the midpoint of vector u,v; the orthogonal unit vector
    return (v + n*hl), orth

def boundarycheck(coord, w, h, d=None):
    # Inputs:
    # coord: the coordinate (x,y) to check; no (x,y,z) compatibility yet
    # w,h: the width and height of the image to set the boundaries
    _2d = len(coord)==2
    oob = 0     # Generate a boolean check for out-of-boundary
    # Check if coordinate is within the boundary
    if _2d:
        if(coord[0]<0 or coord[1]<0 or coord[0]>(w-1) or coord[1]>(h-1)):
            oob = 1
            coord = np.array([1, 1])
    else:
        if(sum(coord<0)>0 or sum(coord>[w-1,h-1,d-1])>0):
            oob = 1
            coord = np.array([1, 1, 1])
    

    # returns the boolean oob (1 if boundary error); coordinates (reset to (1,1) if boundary error)
    return oob, coord.astype(int)

def lengthtoedge(m,orth,img_bin):
    # Inputs:
    # m: the midpoint of a trace of an edge
    # orth: an orthogonal unit vector
    # img_bin: the binary image that the graph is derived from
    
    _2d = len(m) == 2
    if _2d:
        w,h = img_bin.shape         # finds dimensions of img_bin for boundary check
    else:
        w,h,d = img_bin.shape

    check = 0                       # initializing boolean check
    i = 0                           # initializing iterative variable
    while(check==0):                # iteratively check along orthogonal vector to see if the coordinate is either...
        ptcheck = m + i*orth        # ... out of bounds, or no longer within the fiber in img_bin
        ptcheck = ptcheck.astype(int)
        if _2d:
            oob, ptcheck = boundarycheck(ptcheck, w, h)
            Q_edge = img_bin[ptcheck[0],ptcheck[1]] == 0 or oob == 1     #Checks if point in fibre
        else:
            oob, ptcheck = boundarycheck(ptcheck, w, h, d=d)
            Q_edge = img_bin[ptcheck[0],ptcheck[1],ptcheck[2]] == 0 or oob == 1
        if(Q_edge):
            edge = m + (i-1)*orth
            edge = edge.astype(int)
            l1 = edge               # When the check indicates oob or black space, assign width to l1
            check = 1
        else:
            i += 1
    
    check = 0
    i = 0
    while(check == 0):              # Repeat, but following the negative orthogonal vector
        ptcheck = m - i*orth
        ptcheck = ptcheck.astype(int)
        if _2d:
            oob, ptcheck = boundarycheck(ptcheck, w, h)
            Q_edge = img_bin[ptcheck[0],ptcheck[1]] == 0 or oob == 1     #Checks if point in fibre
        else:
            oob, ptcheck = boundarycheck(ptcheck, w, h, d=d)
            Q_edge = img_bin[ptcheck[0],ptcheck[1],ptcheck[2]] == 0 or oob == 1
        if(Q_edge):
            edge = m - (i-1)*orth
            edge = edge.astype(int)
            l2 = edge               # When the check indicates oob or black space, assign width to l1
            check = 1
        else:
            i += 1
    
    # returns the length between l1 and l2, which is the width of the fiber associated with an edge, at its midpoint
    return np.linalg.norm(l1-l2)

#By default, weight is proportional to edge thickness.
#For analysis of electrical networks, volume may be a more appropriate weight. Note that in this case the weight is the inverse resistance (i.e. conductance)
#For analysis of mass transport systems, (i.e. where flow is proportional to cross sectional area), area is a more appropriate weight
#...However, if the mass transport system has flow also proportional to a nodal driving force, the electrical network model is most appropriate.
def assignweights(ge, img_bin, weight_type=None, R_j=0, rho_dim=1):
    # Inputs:
    # ge: a list of pts that trace along a graph edge
    # img_bin: the binary image that the graph is derived from

    # check to see if ge is an empty or unity list, if so, set wt to 1
    if(len(ge)<2):
        pix_width = 10
        wt = 1
    # if ge exists, find the midpoint of the trace, and orthogonal unit vector
    else:
        endindex = len(ge) - 1
        midindex = int(len(ge)/2)
        pt1 = ge[0]
        pt2 = ge[endindex]
        m = ge[midindex]
        midpt, orth = findorthogonal(pt1, pt2)
        m.astype(int)
        pix_width = int(lengthtoedge(m, orth, img_bin)) 
    if(weight_type==None):
        wt = pix_width/10
    elif(weight_type=='VariableWidthConductance'):
        #This is electrical conductance; not graph conductance.
        #This conductance is based on both width and length of edge, as measured from the raw data. rho_dim is resistivity (i.e. ohm pixels)
        length = len(ge)
        if pix_width == 0 or length == 0:
            wt = 1 #Arbitrary. Smallest possible value for a lattice graph. Using zero may cause 0 elements on the weighted Laplacian diagonal, rendering flow problems underdetermined
        else:
            wt = ((length*rho_dim/pix_width**2) + R_j*2)**-1
    elif(weight_type=='FixedWidthConductance'):
        #This conductance is based on length of edge, as measured from data whereas width is supplied as part of rho_dim.
        #rho_dim should be equal resistivity/cross_secitonal area
        length = len(ge)
        if pix_width == 0 or length == 0:
            wt = 1 #Arbitrary. Smallest possible value for a lattice graph. Using zero may cause 0 elements on the weighted Laplacian diagonal, rendering flow problems underdetermined
        else:
            wt = ((length*rho_dim) + R_j*2)**-1
    elif(weight_type=='Resistance'): #Reciprocal of conductance
        length = len(ge)
        if pix_width == 0 or length == 0:
            wt = 1 #Arbitrary. Smallest possible value for a lattice graph. Using zero may cause 0 elements on the weighted Laplacian diagonal, rendering flow problems underdetermined
        else:
            wt = ((length*rho_dim/pix_width**2) + R_j*2)
    elif(weight_type=='Area'):
        length = len(ge)
        if pix_width == 0 or length == 0:
            wt = 1 #Arbitrary. Smallest possible value for a lattice graph. Using zero may cause 0 elements on the weighted Laplacian diagonal, rendering flow problems underdetermined
        else:
            wt = pix_width**2
    else:
        raise TypeError('Invalid weight type')
    
    # returns the width in pixels; the weight which
    return pix_width, wt
