import numpy as np
import sknw
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

from skimage.morphology import skeletonize, skeletonize_3d, binary_closing
from StructuralGT import process_image, GetWeights_3d, error

#Function returns true for names of images
def Q_img(name):
    if (name.endswith('.tiff') or 
        name.endswith('.tif') or
        name.endswith('.jpg') or
        name.endswith('.jpeg') or
        name.endswith('.png') or
        name.endswith('.gif')):
        return True
    else:
        return False

#Function returns lattice points joining 2 other points
def connector(point1, point2):
    vec = point2 - point1
    edge = np.array([point1])
    for i in np.linspace(0,1):
        edge = np.append(edge, np.array([point1 + np.multiply(i,vec)]), axis=0)
    
    edge = edge.astype(int)
    edge = np.unique(edge, axis=0)

    return edge

def canvas_to_G(name):

    canvas = np.load(name)
    G = sknw.build_sknw(canvas.astype(int))

def shift(points):
    if len(points[0]) == 3:
        shift=(np.full((np.shape(points)[0],3),[np.min(points.T[0]),np.min(points.T[1]),np.min(points.T[2])]))
    else:   
        shift=(np.full((np.shape(points)[0],2),[np.min(points.T[0]),np.min(points.T[1])]))

    points = points - shift
    return points

#Shifts points to origin centre
def oshift(points):
    shift = np.full((np.shape(points)[0],3),[np.max(points.T[0])/2,np.max(points.T[1])/2,np.max(points.T[2])/2]) 
    points = points - shift
    return points

#For lists of positions where all elements along one axis have the same value, this returns the same list of positions but with the redundant dimension(s) removed
def dim_red(positions):
    unique_positions = np.asarray(list(len(np.unique(positions.T[i])) for i in range(len(positions.T))))
    redundant = unique_positions == 1
    positions = positions.T[~redundant].T
    return positions

def gsd_to_canvas(gsd_name):
    frame = gsd.hoomd.open(name=gsd_name, mode='rb')[0]
    positions = frame.particles.position.astype(int)
    dims = np.asarray(list(max(positions.T[i])+1 for i in (0,1,2)))
    
    canvas = np.zeros(dims)
    canvas[positions.T[0], positions.T[1], positions.T[2]] = 1
    return canvas

def canvas_to_gsd(canvas, gsd_name):
    positions = np.asarray(np.where(np.asarray(canvas)!=0)).T
    s = gsd.hoomd.Snapshot()
    s.particles.N = len(positions)
    s.particles.types = ['A']
    s.particles.typeid = ['0']*s.particles.N
    s.particles.position = positions

    with gsd.hoomd.open(name=gsd_name, mode='wb') as f:
        f.append(s)
    
def G_to_gsd(G, gsd_name):
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
    
def stack_to_canvas(stack_directory, crop=None):
    img_bin = []
    i=0
    for name in sorted(os.listdir(stack_directory)):
        if Q_img(name):
            img_slice = cv.imread(stack_directory+'/slice'+str(i)+'.tiff',cv.IMREAD_GRAYSCALE)
            img_bin.append(img_slice)
            i=i+1
        else:
            pass
    
    img_bin = np.asarray(img_bin)
    print('Uncropped img_bin has shape ', img_bin.shape)
    if crop != None:
        img_bin = img_bin[crop[0]:crop[1], crop[2]:crop[3], crop[4]:crop[5]]

    img_bin = np.squeeze(img_bin)
    return img_bin



def stack_to_G(stack_directory):
    img_bin = []
    i=0
    for name in sorted(os.listdir(stack_directory)):
        if Q_img(name):
            img_slice = cv.imread(stack_directory+'/slice'+str(i)+'.tiff',cv.IMREAD_GRAYSCALE)
            img_bin.append(img_slice)
            i=i+1
        else:
            pass

    img_bin = np.asarray(img_bin)
    skeleton = skeletonize_3d(img_bin)
    G = sknw.build_sknw(skeleton)

    return G

#Functions returns list of position from a given gsd file. Optionally, it may return a list of positions that only fall within a given set of dimensions, effectively cropping the domain. TODO replace cropping with array masking method
def gsd_to_pos(gsd_name, crop=None):
    frame = gsd.hoomd.open(name=gsd_name, mode='rb')[0]
    positions = frame.particles.position.astype(int)
    
    if crop != None:
        canvas = np.zeros(list((max(positions.T[i])+1) for i in (0,1,2)))
        canvas[tuple(list(positions.T))] = 1
        canvas = canvas[crop[0]:crop[1],
                          crop[2]:crop[3],
                          crop[4]:crop[5]]
       
        positions = np.asarray(np.where(canvas==1)).T

    return positions

#Function takes gsd rendering of a skeleton and returns the list of nodes and edges, as calculated by sknw. Optionally, it may crop. sub=True will reduce the returned graph to the largest connected induced subgraph, resetting node numbers to consecutive integers, starting from 0.
#_2d=True ensures any additional redundant axes from the position list is removed. It does not guarantee a 3d graph
def gsd_to_G(gsd_name, sub=False, _2d=False):#crop=None):
    start = time.time()
    frame = gsd.hoomd.open(name=gsd_name, mode='rb')[0]
    positions = frame.particles.position.astype(int)
    if sum((positions<0).ravel()) != 0:
        positions = shift(positions)
    
    """remove
    if crop != None:
        from numpy import logical_and as a
        p=positions.T
        positions = p.T[a(a(a(a(a(p[0]>=crop[0],p[0]<=crop[1]),p[1]>=crop[2]),p[1]<=crop[3]),p[2]>=crop[4]),p[2]<=crop[5])]
        positions = shift(positions)
    """
    
    if _2d:
        positions = dim_red(positions)
    canvas = np.zeros(list((max(positions.T[i])+1) for i in list(range(min(positions.shape)))))
    canvas[tuple(list(positions.T))] = 1
    canvas = canvas.astype(int)
    print('gsd_to_G canvas has shape ', canvas.shape)
    G = sknw.build_sknw(canvas)
    if sub:
        G = sub_G(G)
    end = time.time()
    print('Ran gsd_to_G in ', end-start, 'for a graph with ', G.vcount(), 'nodes.')
    return G
    
#Function reads, crops and rewrites gsd file. TODO write branch and endpoint data to new gsd file (currently this info is lost).
def gsd_crop(gsd_name, save_name, crop):
    frame = gsd.hoomd.open(name=gsd_name, mode='rb')[0]
    positions = frame.particles.position.astype(int)

    from numpy import logical_and as a
    p=positions.T
    positions = p.T[a(a(a(a(a(p[0]>crop[0],p[0]<crop[1]),p[1]>crop[2]),p[1]<crop[3]),p[2]>crop[4]),p[2]<crop[5])]
    positions_T = positions.T
    positions_T[0] = positions_T[0]
    positions = positions_T.T
    positions = shift(positions)
    s = gsd.hoomd.Snapshot()
    s.particles.N = len(positions)
    s.particles.types = ['A']
    s.particles.typeid = ['0']*s.particles.N
    s.particles.position = positions

    with gsd.hoomd.open(name=save_name, mode='wb') as f:
        f.append(s)
    

#Performs and times compute light averaged GT calcs
def G_analysis_lite(gsd_name):
    from networkx.algorithms.centrality import betweenness_centrality, closeness_centrality, eigenvector_centrality
    from networkx.algorithms import average_node_connectivity, global_efficiency, clustering, average_clustering
    from networkx.algorithms import degree_assortativity_coefficient
    from networkx.algorithms.flow import maximum_flow
    from networkx.algorithms.distance_measures import diameter, periphery
    from networkx.algorithms.wiener import wiener_index

    start = time.time()
    G = gsd_to_G(gsd_name)
    end = time.time()
#   Currently neglected eigenvector centrality as it doesnt easily converge (must change max iterations)

    operations = [global_efficiency, average_clustering, degree_assortativity_coefficient, maximum_flow, diameter, periphery, wiener_index]

    for operation in operations:
        try:
            start = time.time()
            ans = operation(G)
            end = time.time()
            print(str(operation),'calculated as', ans, 'in', end-start)
        except TypeError:
            pass
#Function generates largest connected induced subgraph. Node and edge numbers are reset such that they are consecutive integers, starting from 0
def sub_G(G): 
    print('pre sub has ', G.vcount(), ' nodes')
    components = G.clusters()
    G = components.giant() 
    print('post sub has ', G.vcount(), ' nodes')
   
   # G_sub  = G.subgraph(max(nx.connected_components(G), key=len).copy())
   # G = nx.relabel.convert_node_labels_to_integers(G_sub)
    
    return G

#Function takes a gsd name, generates a graph with gsd_to_G() and resaves a new .gsd file which has some nodewise indices saved to the file
def G_labelling(gsd_name, graph=None, _2d=False):

    positions = gsd.hoomd.open(name=gsd_name, mode='rb')[0].particles.position
    if graph is None:
         start = time.time()
         G = gsd_to_G(gsd_name)
         end = time.time()
    else:
         G = graph

    operations = [G.degree, G.betweenness, G.closeness]
    names = ['Degree', 'Betweenness_Centrality', 'Closeness_Centrality']
    node_positions = np.asarray(G.vs['o'])
    
    save_name = os.path.join(os.path.split(gsd_name)[0],'labelled_'+os.path.split(gsd_name)[1]) #REFERENCE CONCATENATOR
    node_positions = shift(node_positions).astype(int)
    positions = shift(positions).astype(int)
    
    node_origin_shift =(np.full((np.shape(node_positions)[0],3),[np.max(positions.T[0])/2,np.max(positions.T[1])/2,np.max(positions.T[2])/2])) 
    position_origin_shift = (np.full((np.shape(positions)[0],3),[np.max(positions.T[0])/2,np.max(positions.T[1])/2,np.max(positions.T[2])/2]))

    #node_positions = node_positions - node_origin_shift
    #positions = positions - position_origin_shift
    s = gsd.hoomd.Snapshot()
    N = len(positions)
    s.particles.N = N
    s.particles.position = positions
    s.particles.types = ['Edge', 'Node']
    s.particles.typeid = [0]*N
    L = list(max(positions.T[i])*2 for i in (0,1,2))
    s.configuration.box = [L[0], L[1], L[2], 0, 0, 0]
    for name,operation in zip(names,operations):
        s.log['particles/'+name] = [np.NaN]*N
        start = time.time()
        index_list = operation()

        end = time.time()
        print('Ran ', operation, ' in ', end-start)
    
        j=0
        for i,particle in enumerate(positions):
            node_id = np.where(np.all(positions[i] == node_positions, axis=1) == True)[0]
            if len(node_id) == 0: 
                continue
            else:
                s.log['particles/'+name][i] = index_list[node_id[0]]
                s.particles.typeid[i] = 1
                j+=1
    with gsd.hoomd.open(name=save_name, mode='wb') as f:
        f.append(s)
    
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

    #if g._2d:
    #    g.skeleton_3d = np.swapaxes(np.array([g.skeleton]), 0, 1)
        #g.skeleton_3d = np.swapaxes(np.array([g.skeleton]), 2, 1)
    #else:
    #    g.skeleton_3d = g.skeleton
    
    g.skeleton_3d = np.asarray([g.skeleton])
    
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

#Redundant if the GT_Params_noGUI is from the igraph branch 
def igraph_avg_indices(I):
    avg_indices = dict()
    
    operations = [I.diameter, I.density, I.transitivity_undirected, I.assortativity_degree]
    names = ['Diameter', 'Density', 'Clustering', 'Assortativity by degree']

    for operation,name in zip(operations,names):
        start = time.time()
        avg_indices[name] = operation()
        end = time.time()
        print('Calculated ', name, ' in ', end-start)

    return avg_indices

#Saves graph average indices and node indices to 2 separate files
def igraph_calcs(directory, G):
    G = sub_G(G)
    I=ig.Graph.from_networkx(G)
    operations = [I.betweenness, I.closeness, I.degree, I.vertex_connectivity] 
    names = ['Betweeness', 'Closeness', 'Degree']

    for operation,name in zip(operations,names):
        start = time.time()
        np.savetxt(directory+'/'+name+'.csv', operation())
        end=time.time()
        print('Saved ', operation, ' in ', end-start, ' for a graph with ', G.vcount(), ' nodes')
    
    avg_indices = igraph_avg_indices(I)
    
    with open(directory+'/graphwise.csv', 'w') as f:
        for key in avg_indices:
            f.write("%s,%s\n"%(key,avg_indices[key]))
    


"""
REQUIRES GRAPH_TOOL - NOT IMPORTED BY DEFAULT
def benchmark(gsd_name,skel_name):
    start = time.time()
#Generate NetworkX type graph object
    G = gsd_to_G(gsd_name)
    G=sub_G(G)
    end = time.time()

#Benchmark igraph
    I=ig.Graph.from_networkx(G)
    start = time.time()
    print('Nodes are ', I.vcount())
    print('Closeness = ', I.closeness())
    print('Degrees = ', I.degree())
    print('Betweenness = ', I.betweenness())
    end = time.time()
    print("igraph Clo/Deg/Bet calculated in ", end-start)

#Write to .gml so that is can be read by graph-tool.
#Vertex position attribute has to be mapped as three separate atttributes (x,y,z) as gml vertex attributes cannot be arrays
#Other edge and vertex attributes should be deleted
    start = time.time()
    nodes = G.nodes()
    positions = np.asarray(list(G.nodes()[i]['o'] for i in nodes))
    for i,position in enumerate(positions):
        del G.nodes[i]['pts']
        del G.nodes[i]['o']
        G.nodes[i]['x'] = position[0]
        G.nodes[i]['y'] = position[1]
        G.nodes[i]['z'] = position[2]

    for i,j in G.edges():
        del G.edges()[i,j]['pts']
        del G.edges()[i,j]['weight']

    nx.write_graphml(G, skel_name)

    G = gt.load_graph(skel_name)
    end = time.time()
    print("Converted to graph-tool object in ", end-start)

    start = time.time()
    print('Nodes are ', G.vertices())
    print('Closeness = ', gt.closeness(G))
    print('Degrees = ', G.degree_property_map('total'))
    print('Betweenness = ', gt.betweenness(G))
    end = time.time()
    print("graph-tool Clo/Deg/Bet calculated in ", end-start)
"""


#Binarizes stack of experimental images using a set of image processing parameters in options_dict.
#Note this enforces that all images have the same shape as the first image encountered by the for loop.
#(i.e. the first alphanumeric titled image file)
def ExpProcess(directory, options_dict=None):
    
    if options_dict is None:
        options = directory + '/img_options.json'
        with open(options) as f:
            options_dict = json.load(f)
    
    #Check if directory exists
    if not os.path.isdir(directory + '/Binarized'):
        os.mkdir(directory+'/Binarized')

    #Generate
    i=0    
    for name in sorted(os.listdir(directory)):
        if Q_img(name)==False:
            pass
        else:
            img_exp = cv.imread(directory+'/'+name,cv.IMREAD_GRAYSCALE)
            if i == 0: shape = img_exp.shape
            elif img_exp.shape != shape: continue
            _, img_bin, _ = process_image.binarize(img_exp, options_dict)
            plt.imsave(directory+'/'+'Binarized'+'/'+'slice'+str(i)+'.tiff', img_bin, cmap=cm.gray)
            i+=1

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
    start = time.time()
    for i,edge in enumerate(g.Gr.es()):
        ge = edge['pts']
        pix_width, wt = GetWeights_3d.assignweights(ge, g.img_bin, weight_type=weight_type, R_j=R_j, rho_dim=rho_dim)
        edge['pixel width'] = pix_width
        edge['weight'] = wt
    end = time.time()
    
    return g.Gr

def stack_analysis(stack_directory, suffix, ANC=False, crop=None):
     ExpProcess(stack_directory)
     
     skel_name = stack_directory+'/skel_'+suffix+'.gsd'

     start = time.time()
     canvas = stack_to_canvas(stack_directory+'/Binarized', crop)
     skeleton = skeletonize_3d(canvas)
     canvas_to_gsd(skeleton,skel_name) 
     debubble(skel_name)

     debubble_name = os.path.split(skel_name)[0] + '/debubbled_' + os.path.split(skel_name)[1]

     G = gsd_to_G(debubble_name) 
     
     igraph_calcs(stack_directory,G)
     if ANC:
         igraph_ANC(stack_directory, ig.Graph.from_networkx(G)) 

##The following function is a special case of the above G_labelling which takes a weighted graph and returns the weighted Laplacian.
##This operation is important for solving the Kirchhoff equation for electrical networks whose edge is weighted by resistance
##Currently, only igraph is implemented
def weighted_Laplacian(G):
    
    L=np.asarray(G.laplacian(weights='weight'))
    np.save('weighted_laplacian.npy', L)
    return L

#The 'plane' arguement defines the /axis/ which along which the boundary arguements refer to
#Weighted=False enables the unusual case of all edges having the same resistance and can be used to establish the relative effects of geometry and topology
def voltage_distribution(g, plane, boundary1, boundary2, crop=None, I_dim =1,  R_j=0, rho_dim=1):

    print('pre sub has ', g.Gr.vcount(), ' nodes')
    g.Gr = sub_G(g.Gr)
    print('post sub has ', g.Gr.vcount(), ' nodes')
    if R_j != 'infinity':
        g = add_weights(g, crop=crop, weight_type='Conductance', R_j=R_j, rho_dim=rho_dim)
        weight_array = np.asarray(g.Gr.es['weight']).astype(float)
        weight_array = weight_array[~np.isnan(weight_array)]
        g.edge_weights = weight_array
        weight_avg =np.mean(weight_array)
    else:
        g.Gr.es['weight'] = np.ones(g.Gr.ecount())
        weight_avg = 1
  

#Add source and sink nodes:
    source_id = max(g.Gr.vs).index + 1
    sink_id = source_id + 1
    g.Gr.add_vertices(2)
#Add coords for plotting
    #positions = []
    #for i in range(G.vcount()):
    #    if g.G.vs[i]['o'] is None:
    #        pass
    #    else:
    #        positions.append(g.G.vs[i]['o'].ravel())
    
    #positions = np.concatenate(np.asarray(positions)).reshape((len(positions),len(positions[0])))
    
    positions = g.positions
    dims = g.shape
    dim = g.dim
    #dim = len(positions[0])
    #dims = list(max(positions.T[i]) for i in (range(dim)))
    #dims = list(max(np.stack(list(G.vs[i]['o'] for i in range(G.vcount()))).T[j]) for j in (0,1,2)) 
    #mins = list(min(np.asarray(list(G.vs[i]['o'] for i in range(G.vcount())), dtype=object).T[j]) for j in (0,1,2))
    #print(np.asarray(list(G.vs[i]['o'] for i in range(G.vcount()))).T)
    print('Graph has max ', dims)
    axes = np.array([0,1,2])[0:dim]
    indices = axes[axes!=plane]
    plane_centre1 = np.zeros(dim, dtype=int)
    delta = np.zeros(dim, dtype=int)
    delta[plane] = 10 #Arbitrary. Standardize?
    for i in indices: plane_centre1[i] = dims[i]/2
    plane_centre2 = np.copy(plane_centre1)
    plane_centre2[plane] = dims[plane]
    source_coord = plane_centre1 - delta 
    sink_coord = plane_centre2 + delta
    print('source coord is ', source_coord)
    print('sink coord is ', sink_coord)
    g.Gr.vs[source_id]['o'] = source_coord
    g.Gr.vs[sink_id]['o'] = sink_coord

#Connect nodes on a given boundary to the external current nodes
    print('Before connecting external nodes, G has vcount ', g.Gr.vcount())
    for node in g.Gr.vs:
        if node['o'][plane] > boundary1[0] and node['o'][plane] < boundary1[1]:
            g.Gr.add_edges([(node.index, source_id)])
            g.Gr.es[g.Gr.get_eid(node.index,source_id)]['weight'] = weight_avg
            g.Gr.es[g.Gr.get_eid(node.index,source_id)]['pts'] = connector(source_coord,node['o'])
        if node['o'][plane] > boundary2[0] and node['o'][plane] < boundary2[1]:
            g.Gr.add_edges([(node.index, sink_id)])
            g.Gr.es[g.Gr.get_eid(node.index,sink_id)]['weight'] = weight_avg 
            g.Gr.es[g.Gr.get_eid(node.index,sink_id)]['pts'] = connector(sink_coord,node['o'])

#Write skeleton connected to external node
    print(g.Gr.is_connected(), ' connected')
    print('After connecting external nodes, G has vcount ', g.Gr.vcount())
    connected_name = os.path.split(g.gsd_name)[0] + '/connected_' + os.path.split(g.gsd_name)[1] 
    #connected_name = g.stack_directory + '/connected_' + g.gsd_name 
    G_to_gsd(g.Gr, connected_name)

    L = weighted_Laplacian(g.Gr)
    I = np.zeros(sink_id+1)
    print(I.shape,'I')
    print(L.shape, 'L')
    I[source_id] = I_dim
    I[sink_id] = -I_dim
    np.save(g.stack_dir+'/L.npy',L)
    np.save(g.stack_dir+'/I.npy',I)
    V = np.matmul(np.linalg.pinv(L, hermitian=True),I)
    #VC =np.linalg.solve(L,I)
    np.save(g.stack_dir+'/V.npy',V)
    
    g.L = L
    g.V = V
    g.I = I

    return g

#Labelling function which takes an attribute calculating function and its relevant parameters (usually gsd, img_bin and, optionally, crop)
#The labelling function calls the attribute calculating function so that the graph and its nodes' attributes are returned
#The labelling funciton appends the attribute to the graph and rewrites the gsd
#Note that all attribute calculating functions must return the attribute tensor and the graph which is to be labelled
#The gsd_name given in *args is the file in which the unlabelled graph should be extracted from.

#Labelling function which takes a graph object, node attribute and writes their values to a new .gsd file. 
def Node_labelling(g, attribute, attribute_name, filename):
    """
    Function saves a new .gsd which has the graph in g.Gr labelled with the node attributes in attribute
    """
    
    assert g.Gr.vcount() == len(attribute)
    
    #save_name = os.path.split(prefix)[0] + '/'+attribute_name + os.path.split(prefix)[1]
    save_name = g.stack_dir + '/' + filename
    if os.path.exists(save_name):
        mode = 'rb+'
    else:
        mode = 'wb'

    f = gsd.hoomd.open(name=save_name, mode=mode)
    
    #Must segregate position list into a node_position section and edge_position
    node_positions = np.asarray(list(g.Gr.vs()[i]['o'] for i in range(g.Gr.vcount())))
    positions = node_positions
    for edge in g.Gr.es():
        positions=np.vstack((positions,edge['pts']))
    positions = np.unique(positions, axis=0)
    if g._2d:
        node_positions = np.hstack((np.zeros((len(node_positions),1)),node_positions))
        positions = np.hstack((np.zeros((len(positions),1)),positions))

    #node_positions = base.shift(node_positions)
    #positions = base.shift(positions)
    s = gsd.hoomd.Snapshot()
    N = len(positions)
    s.particles.N = N
    s.particles.position = positions
    s.particles.types = ['Edge', 'Node']
    s.particles.typeid = [0]*N
    L = list(max(positions.T[i])*2 for i in (0,1,2))
    #s.configuration.box = [L[0]/2, L[1]/2, L[2]/2, 0, 0, 0]
    s.configuration.box = [1,1,1,0,0,0]
    s.log['particles/'+attribute_name] = [np.NaN]*N
    start = time.time()

    j=0
    for i,particle in enumerate(positions):
        node_id = np.where(np.all(positions[i] == node_positions, axis=1) == True)[0]
        if len(node_id) == 0: 
            continue
        else:
            s.log['particles/'+attribute_name][i] = attribute[node_id[0]]
            s.particles.typeid[i] = 1
            j+=1
    
    f.append(s)


#Function returns the principal moments of the given network's gyration tensor.
#Components in the sum forming the components of the gyration tensor are defined by shortest paths between pairs of nodes, not node pairs.
#sampling arguement allows moments to be estimated from a subset of node pairs
###NOTES ON TIMING###
#Node subset/Node total    Time
#~500/3000                 ~20 s
#~1800/5500                ~10 min

def gyration_moments(G, weighted=True, sampling=1):
#Serial implementation
    Ax=0
    Ay=0
    node_count = np.asarray(list(range(G.vcount())))
    mask = np.random.rand(G.vcount()) > (1-sampling)
    trimmed_node_count = node_count[mask]
    for i in trimmed_node_count:
        for j in trimmed_node_count:
            if i >= j:    #Symetric matrix
                continue
            path = G.get_shortest_paths(i,to=j)
            Ax_term = 0
            Ay_term = 0
            for hop_s,hop_t in zip(path[0][0:-1],path[0][1::]):
                if weighted:
                    weight = G.es[G.get_eid(hop_s,hop_t)]['weight']
                else:
                    weight = 1
                Ax_term = Ax_term + ((weight*(int(G.vs[hop_s]['o'][0])-int(G.vs[hop_t]['o'][0])))**2)
                Ay_term = Ay_term + ((weight*(int(G.vs[hop_s]['o'][1])-int(G.vs[hop_t]['o'][1])))**2)
            Ax = Ax + (Ax_term)
            Ay = Ay + (Ay_term)

    return Ax, Ay

def gyration_moments_2(G, sampling=1):
#Serial implementation
    Ax=0
    Ay=0
    node_count = np.asarray(list(range(G.vcount())))
    mask = np.random.rand(G.vcount()) > (1-sampling)
    trimmed_node_count = node_count[mask]
    for i in trimmed_node_count:
        for j in trimmed_node_count:
            if i >= j:    #Symetric matrix
                continue
            path = G.get_shortest_paths(i,to=j)
            Ax_term = 0
            Ay_term = 0
            for hop_s,hop_t in zip(path[0][0:-1],path[0][1::]):
                weight = G.es[G.get_eid(hop_s,hop_t)]['weight']
                Ax_term = Ax_term + ((weight*(int(G.vs[hop_s]['o'][0])-int(G.vs[hop_t]['o'][0]))))
                Ay_term = Ay_term + ((weight*(int(G.vs[hop_s]['o'][1])-int(G.vs[hop_t]['o'][1]))))
            Ax = Ax + (Ax_term)
            Ay = Ay + (Ay_term)

    return Ax, Ay

def parallel_gyration(G):
        #Parallel implementation
    from mpi4py import MPI
    import numpy as np
    import argparse
    comm = MPI.COMM_WORLD
    rank = comm.rank
    size = comm.size
    
    if comm.rank == 0:
        #Function distributes nodes amongst cores such that each core has approximately equal number of shortest paths
        #This doesn't imply equal number of nodes
        def path_partition(node_count, core_count):
            path_count = int(node_count*(node_count-1)/2)
            path_per_core = np.floor(path_count/core_count)
            NRI = dict()

            first_node = 0
            for i in range(core_count):
                paths = 0 #Current length of path list
                nodes = [] #List of nodes corresponding to this path list
                for n in range(first_node, node_count):
                    if paths >= (path_per_core): #If path list for a given core is full, move to next core
                        continue
                    nodes = nodes + [n]
                    paths = paths + (node_count - n) #General formula for number of paths included by a given node
                    first_node = n + 1
                NRI[str(i)] = nodes
            return NRI
        
        node_count = G.vcount()

        G_NRI = [G,path_partition(node_count,size)]
        Ax_sum = np.array([0])
        Ay_sum = np.array([0])
    else:
        G_NRI = None
        Ax_sum = None
        Ay_sum = None

    #Save global variables that are broadcasted by the root rank
    #G_NRI is list of [G,NRI]
    G_NRI = comm.bcast(G_NRI, root=(0))
    G = G_NRI[0]
    NRI = G_NRI[1]

    Ax=0
    Ay=0

    node_count = G.vcount()
    node_range = NRI[str(rank)]
    for i in node_range:
        for j in range(node_count):
            if i >= j:    #Symetric matrix
                continue
            path = G.get_shortest_paths(i,to=j)
            Ax_term = 0
            Ay_term = 0
            for hop_s,hop_t in zip(path[0][0:-1],path[0][1::]):
                weight = G.es[G.get_eid(hop_s,hop_t)]['weight']
                Ax_term = Ax_term + ((weight*(int(G.vs[hop_s]['o'][0])-int(G.vs[hop_t]['o'][0])))**2)
                Ay_term = Ay_term + ((weight*(int(G.vs[hop_s]['o'][1])-int(G.vs[hop_t]['o'][1])))**2)
            Ax = Ax + (Ax_term)
            Ay = Ay + (Ay_term)

    Ax = np.array([Ax])
    Ay = np.array([Ay])
    comm.Reduce([Ax,MPI.DOUBLE],[Ax_sum,MPI.DOUBLE],root=0)
    comm.Reduce([Ay,MPI.DOUBLE],[Ay_sum,MPI.DOUBLE],root=0)
    #Collect Ai terms from all ranks and sum
    if comm.rank == 0:
        print(Ax_sum/Ay_sum)
        return Ax_sum, Ay_sum

