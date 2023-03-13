import numpy as np
#import sknwEdits as sknw
import igraph as ig
import gsd.hoomd
import pandas as pd
import os
import time
import shutil
import cv2 as cv
import json
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import csv

from skimage.morphology import skeletonize, skeletonize_3d, binary_closing, remove_small_objects
from StructuralGTEdits import process_image, GetWeights_3d, error, convert, skel_ID, sknwEdits


def read(name, read_type):
    """For raising an error when a file does not exist because cv.imread does
    not do this.
    """
    out = cv.imread(name, read_type)
    if out is None:
        raise ValueError(name + ' does not exist')
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
    if (name.endswith('.tiff') or
        name.endswith('.tif') or
        name.endswith('.jpg') or
        name.endswith('.jpeg') or
        name.endswith('.png') or
            name.endswith('.gif')):
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
        edge = np.append(edge, np.array([point1 + np.multiply(i, vec)]),
                         axis=0)
    edge = edge.astype(int)
    edge = np.unique(edge, axis=0)

    return edge


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
            _shift = (np.full((np.shape(points)[0], 2),
                              [np.min(points.T[0]), np.min(points.T[1])]))
        else:
            _shift = (np.full((np.shape(points)[0], 3),
                              [np.min(points.T[0]),
                               np.min(points.T[1]),
                               np.min(points.T[2])]))

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
            _shift = np.full((np.shape(points)[0], 2),
                             [np.max(points.T[0])/2, np.max(points.T[1])/2])
            _shift = np.full((np.shape(points)[0], 3),
                             [np.max(points.T[0])/2,
                              np.max(points.T[1])/2,
                              np.max(points.T[2])/2])

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
            if (point[0] < crop[0] or
                point[0] > crop[1] or
                point[1] < crop[2] or
                    point[1] > crop[3]):
                return False
            return True
    else:
        for point in points:
            if (point[0] < crop[0] or
                point[0] > crop[1] or
                point[1] < crop[2] or
                point[1] > crop[3] or
                point[2] < crop[4] or
                    point[2] > crop[5]):
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

    unique_positions = np.asarray(list(len(np.unique(positions.T[i]))
                                  for i in range(len(positions.T))))
    redundant = unique_positions == 1
    positions = positions.T[~redundant].T

    return positions


def G_to_gsd(G, gsd_name):
    """Remove?"""
    dim = len(G.vs[0]['o'])

    positions = np.asarray(list(G.vs[i]['o'] for i in range(G.vcount())))
    for i in range(G.ecount()):
        positions = np.append(positions,G.es[i]['pts'], axis=0)

    N = len(positions)
    if dim==2:
        positions = np.append([np.zeros(N)],positions.T,axis=0).T

    s = gsd.hoomd.Snapshot()
    s.particles.N = N
    s.particles.types = ['A']
    s.particles.typeid = ['0']*N
    s.particles.position = positions

    with gsd.hoomd.open(name=gsd_name, mode='wb') as f:
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
    frame = gsd.hoomd.open(name=gsd_name, mode='rb')[0]
    positions = shift(frame.particles.position.astype(int))[0]
    if crop is not None:
        from numpy import logical_and as a
        p = positions.T
        positions = p.T[a(a(a(p[1] >= crop[0],
                              p[1] <= crop[1]),
                            p[2] >= crop[2]),
                        p[2] <= crop[3])]
        positions = shift(positions)[0]

    if sum((positions < 0).ravel()) != 0:
        positions = shift(positions)[0]

    if _2d:
        positions = dim_red(positions)
        new_pos = np.zeros((positions.T.shape))
        new_pos[0] = positions.T[0]
        new_pos[1] = positions.T[1]
        positions = new_pos.T.astype(int)

    canvas = np.zeros(list((max(positions.T[i])+1)
                           for i in list(range(min(positions.shape)))))
    canvas[tuple(list(positions.T))] = 1
    canvas = canvas.astype(int)
    print('gsd_to_G canvas has shape ', canvas.shape)

    G = sknwEdits.build_sknw(canvas)

    if sub:
        G = sub_G(G)

    return G

#Function generates largest connected induced subgraph. Node and edge numbers are reset such that they are consecutive integers, starting from 0
def sub_G(G): 
    print('pre sub has ', G.vcount(), ' nodes')
    components = G.clusters()
    G = components.giant() 
    print('post sub has ', G.vcount(), ' nodes')
   
   # G_sub  = G.subgraph(max(nx.connected_components(G), key=len).copy())
   # G = nx.relabel.convert_node_labels_to_integers(G_sub)
    
    return G

#GT_Params_noGUI is a modified copy of the original SGT .py file, with the GUI modules removed    
def write_averaged(gsd_name):
    import GT_Params_noGUI
    
    start = time.time()
    G = gsd_to_G(gsd_name)
    end = time.time()
    G = sub_G(G)
    
    start = time.time()
    data = GT_Params_noGUI.run_GT_calcs(G,1,1,1,1,1,1,1,1,0,1,1,0)
    end = time.time()
    print('Ran GT_Params in', end-start, 'for a graph with ', G.vcount(), 'nodes')
    datas = pd.DataFrame(data)
    datas.to_csv(gsd_name + 'Averaged_indices.csv')

def debubble(g, elements):
    if not isinstance(elements,list): raise error.StructuralElementError
 
    start = time.time()
    g.gsd_name = g.gsd_dir + '/debubbled_' + os.path.split(g.gsd_name)[1]
    
    canvas = g.img_bin
    for elem in elements:
        canvas = skeletonize_3d(canvas)/255
        canvas = binary_closing(canvas, selem=elem)

    g.skeleton = skeletonize_3d(canvas)/255

    if g._2d:
        g.skeleton_3d = np.swapaxes(np.array([g.skeleton]), 2, 1)
        g.skeleton_3d = np.asarray([g.skeleton])
    else:
        g.skeleton_3d = np.asarray(g.skeleton)
    
    positions = np.asarray(np.where(g.skeleton_3d!=0)).T
    with gsd.hoomd.open(name=g.gsd_name, mode='wb') as f:
        s = gsd.hoomd.Snapshot()
        s.particles.N = int(sum(g.skeleton_3d.ravel()))
        s.particles.position = positions 
        s.particles.types = ['A']
        s.particles.typeid = ['0']*s.particles.N
        f.append(s)
    end = time.time()
    print('Ran debubble in ', end-start, 'for an image with shape ', g.skeleton_3d.shape)
    
    return g

# Currently works for 2D only (Is just a reproduction of Drew's method)
def merge_nodes(g, disk_size):

    start = time.time()
    g.gsd_name = g.gsd_dir + '/merged_' + os.path.split(g.gsd_name)[1]
    
    canvas = g.skeleton
    g.skeleton = skel_ID.merge_nodes(canvas, disk_size)

    if g._2d:
        g.skeleton_3d = np.swapaxes(np.array([g.skeleton]), 2, 1)
        g.skeleton_3d = np.asarray([g.skeleton])
    else:
        g.skeleton_3d = np.asarray(g.skeleton)
    
    positions = np.asarray(np.where(g.skeleton_3d!=0)).T
    with gsd.hoomd.open(name=g.gsd_name, mode='wb') as f:
        s = gsd.hoomd.Snapshot()
        s.particles.N = int(sum(g.skeleton_3d.ravel()))
        s.particles.position = positions 
        s.particles.types = ['A']
        s.particles.typeid = ['0']*s.particles.N
        f.append(s)
    end = time.time()
    print('Ran merge in ', end-start, 'for an image with shape ', g.skeleton_3d.shape)

    return g

def prune(g, size):

    start = time.time()
    g.gsd_name = g.gsd_dir + '/pruned_' + os.path.split(g.gsd_name)[1]
    
    canvas = g.skeleton
    g.skeleton = skel_ID.pruning(canvas, size)

    if g._2d:
        g.skeleton_3d = np.swapaxes(np.array([g.skeleton]), 2, 1)
        g.skeleton_3d = np.asarray([g.skeleton])
    else:
        g.skeleton_3d = np.asarray(g.skeleton)
    
    positions = np.asarray(np.where(g.skeleton_3d!=0)).T
    with gsd.hoomd.open(name=g.gsd_name, mode='wb') as f:
        s = gsd.hoomd.Snapshot()
        s.particles.N = int(sum(g.skeleton_3d.ravel()))
        s.particles.position = positions 
        s.particles.types = ['A']
        s.particles.typeid = ['0']*s.particles.N
        f.append(s)
    end = time.time()
    print('Ran prune in ', end-start, 'for an image with shape ', g.skeleton_3d.shape)

    return g

def remove_objects(g, size):

    start = time.time()
    g.gsd_name = g.gsd_dir + '/cleaned_' + os.path.split(g.gsd_name)[1]
    
    canvas = g.skeleton
    g.skeleton = remove_small_objects(canvas, size, connectivity=2)

    if g._2d:
        g.skeleton_3d = np.swapaxes(np.array([g.skeleton]), 2, 1)
        g.skeleton_3d = np.asarray([g.skeleton])
    else:
        g.skeleton_3d = np.asarray(g.skeleton)
    
    positions = np.asarray(np.where(g.skeleton_3d!=0)).T
    with gsd.hoomd.open(name=g.gsd_name, mode='wb') as f:
        s = gsd.hoomd.Snapshot()
        s.particles.N = int(sum(g.skeleton_3d.ravel()))
        s.particles.position = positions 
        s.particles.types = ['A']
        s.particles.typeid = ['0']*s.particles.N
        f.append(s)
    end = time.time()
    print('Ran remove objects in ', end-start, 'for an image with shape ', g.skeleton_3d.shape)



def igraph_ANC(directory, I):
    start = time.time()
    vclist = []

    for node_i in I.vs:
        for node_j in I.vs:
            if node_i.index == node_j.index: continue
            if I.are_connected(node_i, node_j): continue
            cut = I.vertex_connectivity(source=node_i.index, target = node_j.index)
            vclist.append(cut)

    ANC = np.mean(np.asarray(vclist))
    end = time.time()
    np.savetxt(directory+'/ANC.csv',ANC)
    print('ANC calculated as ', ANC, ' in ', end-start) 
    
    return ANC

#Skeletonize=False enables unusual case of writing binary stack to gsd without skeletonizing. Effective for creating direct 3d reconstruction.
#Takes directory where stack is located, and a gsd write filename
#Note when rotate=None, the crop acts upon an origin cornered image but when rotate != None, the image is origin centred and so the crop may contain -ve elements
def stack_to_gsd(stack_directory, gsd_name, crop=None, skeleton=True, rotate=None):
    start = time.time()
    img_bin=[]
    #Initilise i such that it starts at the lowest number belonging to the images in the stack_directory
    #First require boolean mask to filter out non image files
    olist = np.asarray(sorted(os.listdir(stack_directory)))
    mask = list(Q_img(olist[i]) for i in range(len(olist)))
    if len(mask) == 0:
        raise error.ImageDirectoryError(stack_directory)
    name = sorted(olist[mask])[0] #First name
    i = int(os.path.splitext(name)[0][5:]) #Strip file type and 'slice' then convert to int
    #Generate 3d (or 2d) array from stack
    for name in sorted(os.listdir(stack_directory)):
        if Q_img(name):
            img_slice = cv.imread(stack_directory+'/slice'+str(i)+'.tiff',cv.IMREAD_GRAYSCALE)
            if rotate:
                image_center = tuple(np.array(img_slice.shape[1::-1]) / 2)
                rot_mat = cv.getRotationMatrix2D(image_center, rotate, 1.0)
                img_slice = cv.warpAffine(img_slice, rot_mat, img_slice.shape[1::-1], flags=cv.INTER_LINEAR)
                upper_directory = os.path.split(stack_directory)[0]
                plt.imsave(upper_directory + '/rotated_image.tiff', img_slice, cmap=cm.gray)
            img_bin.append(img_slice)
            i=i+1
        else:
            pass
    positions = np.asarray(np.where(np.asarray(img_bin) != 0)).T
    positions = shift(positions)
    if rotate and crop:
        positions = oshift(positions)        
        from numpy import logical_and as a
        p = positions.T
        positions = p.T[a(a(a(a(a(p[0]>=crop[0],p[0]<=crop[1]),p[1]>=crop[2]),p[1]<=crop[3]),p[2]>=crop[4]),p[2]<=crop[5])]
        positions = shift(positions)

    if crop is not None and rotate is None:
        from numpy import logical_and as a
        p = positions.T
        positions = p.T[a(a(a(a(a(p[0]>=crop[0],p[0]<=crop[1]),p[1]>=crop[2]),p[1]<=crop[3]),p[2]>=crop[4]),p[2]<=crop[5])]

    positions = positions.astype(int)
    dims = np.asarray(list(max(positions.T[i])+1 for i in (0,1,2)))
    canvas = np.zeros(dims)
    canvas[positions.T[0], positions.T[1], positions.T[2]] = 1
    img_bin = canvas

    #Roll axes such that z=0 for all positions when the graph is 2D
    img_bin = np.swapaxes(img_bin, 0, 2)
    if skeleton:
        img_bin = skeletonize_3d(np.asarray(img_bin))
    else:
        img_bin = np.asarray(img_bin)
    positions = np.asarray(np.where(img_bin != 0)).T
   


    with gsd.hoomd.open(name=gsd_name, mode='wb') as f:
        s = gsd.hoomd.Snapshot()
        s.particles.N = len(positions)
        s.particles.position = shift(positions)
        s.particles.types = ['A']
        s.particles.typeid = ['0']*s.particles.N
        f.append(s)
    end = time.time()
    print('Ran stack_to_gsd() in ', end-start, 'for gsd with ', len(positions), 'particles')

def add_weights(g, weight_type=None, R_j=0, rho_dim=1):
    if not isinstance(weight_type,list) and weight_type is not None: raise TypeError('weight_type must be list, even if single element')
    for _type in weight_type:
        for i,edge in enumerate(g.Gr.es()):
            ge = edge['pts']
            pix_width, wt = GetWeights_3d.assignweights(ge, g.img_bin, weight_type=_type, R_j=R_j, rho_dim=rho_dim)
            edge['pixel width'] = pix_width
            if _type == 'VariableWidthConductance' or _type == 'FixedWidthConductance': _type_name = 'Conductance'
            else: _type_name = _type
            edge[_type_name] = wt
            
    return g.Gr


def gyration_moments_3(G, sampling=1, weighted=True):
    Ax=0
    Ay=0
    Axy=0
    node_count = np.asarray(list(range(G.vcount())))
    mask = np.random.rand(G.vcount()) > (1-sampling)
    trimmed_node_count = node_count[mask]
    for i in trimmed_node_count:
        for j in trimmed_node_count:
            if i >= j:    #Symetric matrix
                continue
            
            if weighted:
                path = G.get_shortest_paths(i,to=j, weights='Resistance')
            else:
                path = G.get_shortest_paths(i,to=j)
            Ax_term  = 0
            Ay_term  = 0
            Axy_term = 0
            for hop_s,hop_t in zip(path[0][0:-1],path[0][1::]):
                if weighted:
                    weight = G.es[G.get_eid(hop_s,hop_t)]['Conductance']
                else:
                    weight = 1
                Ax_term  = Ax_term  + weight*(((G.vs[hop_s]['o'][0]).astype(float) - (G.vs[hop_t]['o'][0]).astype(float))**2)
                Ay_term  = Ay_term  + weight*(((G.vs[hop_s]['o'][1]).astype(float) - (G.vs[hop_t]['o'][1]).astype(float))**2)
                Axy_term = Axy_term + weight*(((G.vs[hop_s]['o'][1]).astype(float) - (G.vs[hop_t]['o'][1].astype(float))) * ((G.vs[hop_s]['o'][0]).astype(float) - (G.vs[hop_t]['o'][0]).astype(float)))
            Ax  = Ax  + (Ax_term)
            Ay  = Ay  + (Ay_term)
            Axy = Axy + (Axy_term)
            A = np.array([[Ax,Axy,0],[Axy,Ay,0],[0,0,0]])/(len(trimmed_node_count)**2)
    return A

def from_gsd(filename, frame=0):
    """
    Function returns a Network object stored in a given .gsd file
    Assigns parent directory to filename, dropping last 2 subdirectories.
    I.e. assumes filename given as ../...../dir/Binarized/name.gsd
    This is why the Network object never calls its .binarize() method in this function

    Currently only assigns node positions as attributes.
    TODO: Assign edge position attributes if neccessary
    """
    _dir = os.path.split(os.path.split(filename)[0])[0]
    N = network.Network(_dir)
    f = gsd.hoomd.open(name=filename, mode='rb')[frame]
    rows =   f.log['Adj_rows']
    cols =   f.log['Adj_cols']
    values = f.log['Adj_values']
    A = convert.to_sparse(rows, cols, values)
    G = ig.Graph()
    N.Gr = G.Weighted_Adjacency(A)

    node_pos = f.particles.position[f.particles.typeid == 1]

    assert len(node_pos) == N.Gr.vcount()

    N.Gr.vs['o'] = node_pos

    return N

def tripletise(i):
    if len(str(i))==3: return str(i)
    elif len(str(i))==2: return '0' + str(i)
    elif len(str(i))==1: return '00' + str(i)
    else: raise ValueError

#1-2-3 and 3-2-1 not double counted
#but 1-2-3 and 1-3-2 are double counted
def loops(Gr, n):
    A = np.array(Gr.get_adjacency().data, dtype=np.single)
    for _ in range(n):
        A = np.power(A,A)

    return np.trace(A)/2
