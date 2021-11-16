import numpy as np
import sknw
import igraph as ig
import networkx as nx
import graph_tool.all as gt
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

from skimage.morphology import skeletonize, skeletonize_3d
from StructuralGT import process_image
import GetWeights_3d

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
    shift=(np.full((np.shape(points)[0],3),[np.min(points.T[0]),np.min(points.T[1]),np.min(points.T[2])]))
    points = points - shift
    return points

#Shifts points with negative entries such that all positions become positive
def nshift(points):
    shift=(np.full((np.shape(points)[0],3),[np.min(points.T[0]),np.min(points.T[1]),np.min(points.T[2])]))
    points = points - shift
    print(shift)
    return points

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
    positions = np.asarray(list(G.vs[i]['o'] for i in range(G.vcount())))
    for i in range(G.ecount()):
        positions = np.append(positions,G.es[i]['pts'], axis=0)

    s = gsd.hoomd.Snapshot()
    s.particles.N = len(positions)
    s.particles.types = ['A']
    s.particles.typeid = ['0']*s.particles.N
    s.particles.position = positions

    with gsd.hoomd.open(name=gsd_name, mode='wb') as f:
        f.append(s)
    
def stack_to_canvas(stack_directory, crop=False):
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
    if crop != False:
        img_bin = img_bin[crop[0]:crop[1], crop[2]:crop[3], crop[4]:crop[5]]

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
def gsd_to_pos(gsd_name, crop=False):
    frame = gsd.hoomd.open(name=gsd_name, mode='rb')[0]
    positions = frame.particles.position.astype(int)
    
    if crop != False:
        canvas = np.zeros(list((max(positions.T[i])+1) for i in (0,1,2)))
        canvas[tuple(list(positions.T))] = 1
        canvas = canvas[crop[0]:crop[1],
                          crop[2]:crop[3],
                          crop[4]:crop[5]]
       
        positions = np.asarray(np.where(canvas==1)).T

    return positions

#Function takes gsd rendering of a skeleton and returns the list of nodes and edges, as calculated by sknw. Optionally, it may crop. sub=True will reduce the returned graph to the largest connected induced subgraph, resetting node numbers to consecutive integers, starting from 0.
def gsd_to_G(gsd_name, crop=False, sub=False):
    start = time.time()
    frame = gsd.hoomd.open(name=gsd_name, mode='rb')[0]
    positions = frame.particles.position.astype(int)
    print(positions)
    if sum((positions<0).ravel()) != 0:
        positions = nshift(positions)
    if crop != False:
        from numpy import logical_and as a
        p=positions.T
        positions = p.T[a(a(a(a(a(p[0]>crop[0],p[0]<crop[1]),p[1]>crop[2]),p[1]<crop[3]),p[2]>crop[4]),p[2]<crop[5])]
        positions = shift(positions)

    print(positions)
    canvas = np.zeros(list((max(positions.T[i])+1) for i in (0,1,2)))
    canvas[tuple(list(positions.T))] = 1
    canvas = canvas.astype(int)
    print('gsd_to_G canvas has shape ', canvas.shape)
    G = sknw.build_sknw(canvas)
    if sub:
        G = sub_G(G)
    end = time.time()
    print('Ran gsd_to_G in ', end-start, 'for a graph with ', len(G.nodes()), 'nodes.')
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
    
#Compute heavy calculations
def G_analysis(G):
    from networkx.algorithms.connectivity.connectivity import average_node_connectivity as anc
    #Obtain the largest connected induced subgraph of G
    G_sub  = G.subgraph(max(nx.connected_components(G), key=len).copy()) 
    return anc(G_sub)

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
    print('Ran gsd_to_G() in', end-start)
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
    G_sub  = G.subgraph(max(nx.connected_components(G), key=len).copy())
    G = nx.relabel.convert_node_labels_to_integers(G_sub)
    
    return G

#Function takes a gsd name, generates a graph with gsd_to_G() and resaves a new .gsd file which has some nodewise indices saved to the file
def G_labelling(gsd_name, graph=None, tool='networkx'):
    from networkx.algorithms.centrality import betweenness_centrality, closeness_centrality

    positions = gsd.hoomd.open(name=gsd_name, mode='rb')[0].particles.position
    if graph is None:
         start = time.time()
         G = gsd_to_G(gsd_name)
         end = time.time()
         print('Ran gsd_to_G() in', end-start)    
    else:
         G = graph

    if tool=='networkx':
        operations = [nx.degree, nx.clustering, betweenness_centrality, closeness_centrality]
        names = ['Degree', 'Clustering', 'Betweenness_Centrality', 'Closeness_Centrality']
        node_positions = np.asarray(list(G.nodes()[i]['o'] for i in np.arange(len(G.nodes()))))
    elif tool=='igraph':
        G = ig.Graph.from_networkx(G)
        operations = [G.degree, G.betweenness, G.closeness]
        names = ['Degree', 'Betweenness_Centrality', 'Closeness_Centrality']
        node_positions = np.asarray(G.vs['o'])
    else:
        print('invalid tool arguement')
    
    save_name = os.path.split(gsd_name)[0] + '/labelled_' + os.path.split(gsd_name)[1]
    f = gsd.hoomd.open(name=save_name, mode='wb')

    

    node_positions = shift(node_positions).astype(int)
    positions = shift(positions).astype(int)
    
    node_origin_shift =(np.full((np.shape(node_positions)[0],3),[np.max(positions.T[0])/2,np.max(positions.T[1])/2,np.max(positions.T[2])/2])) 
    position_origin_shift = (np.full((np.shape(positions)[0],3),[np.max(positions.T[0])/2,np.max(positions.T[1])/2,np.max(positions.T[2])/2]))

    #node_positions = node_positions - node_origin_shift
    #positions = positions - position_origin_shift
    print(node_positions)
    print(positions)
    s = gsd.hoomd.Snapshot()
    N = len(positions)
    s.particles.N = N
    s.particles.position = positions
    s.particles.types = ['Edge', 'Node']
    s.particles.typeid = [0]*N
    L = list(max(positions.T[i])*2 for i in (0,1,2))
    s.configuration.box = [L[0], L[1], L[2], 0, 0, 0]
    G = ig.Graph.from_networkx(G)
    for name,operation in zip(names,operations):
        s.log['particles/'+name] = [np.NaN]*N
        start = time.time()
        if tool=='networkx':
            index_list = operation(G)
        elif tool=='igraph':
            index_list = operation()

        end = time.time()
        print('Ran ', operation, ' in ', end-start)
    
        for i,particle in enumerate(positions):
            for j,node in enumerate(node_positions):
                if sum(node == particle) == 3:
                    s.log['particles/'+name][i] = index_list[j]
                    s.particles.typeid[i] = 1

    f.append(s)
    
#GT_Params_noGUI is a modified copy of the original SGT .py file, with the GUI modules removed    
def write_averaged(gsd_name):
    import GT_Params_noGUI
    
    start = time.time()
    G = gsd_to_G(gsd_name)
    end = time.time()
    print('Ran gsd_to_G() in ', end-start, 'for a graph with ', len(G.nodes()), 'nodes')
    G = sub_G(G)
    
    start = time.time()
    data,klist,Tlist,BCdist,CCdist,ECdist = GT_Params_noGUI.run_GT_calcs(G,1,1,1,1,1,1,1,1,0,1,1,0)
    end = time.time()
    print('Ran GT_Params in', end-start, 'for a graph with ', len(G.nodes()), 'nodes')
    datas = pd.DataFrame(data)
    datas.to_csv(gsd_name + 'Averaged_indices.csv')

def debubble(gsd_name):
    from skimage.morphology import binary_closing, ball, skeletonize_3d
    start = time.time()
    #First rewrite the gsd from position to image space
    frame = gsd.hoomd.open(name=gsd_name, mode='rb')[0]
    positions = frame.particles.position.astype(int)
    shift = -1+(np.full((np.shape(positions)[0],3),[np.min(positions.T[0]),np.min(positions.T[1]),np.min(positions.T[2])]))
    positions = positions - shift
    canvas=np.zeros(list(max(positions.T[i])+3 for i in (0,1,2)))
    canvas[tuple(list(positions.T))] = 1
    #Canvas and positions are all positive
    ball_sizes = [4,2,6] 
    #Fill in all gaps. Consider successive selem passes.
    canvas = binary_closing(canvas, selem=ball(ball_sizes[0]))
    canvas = skeletonize_3d(canvas)/255
    canvas = binary_closing(canvas, selem=ball(ball_sizes[1]))
    canvas = skeletonize_3d(canvas)/255
    canvas = binary_closing(canvas, selem=ball(ball_sizes[2]))
    
    
    reskel =skeletonize_3d(canvas)/255
    
    name = os.path.split(gsd_name)[0] + '/debubbled_' + os.path.split(gsd_name)[1]
    with gsd.hoomd.open(name=name, mode='wb') as f:
        s = gsd.hoomd.Snapshot()
        s.particles.N = int(sum(sum(sum(reskel))))
        s.particles.position = np.asarray(np.where(reskel!=0)).T
        s.particles.types = ['A']
        s.particles.typeid = ['0']*s.particles.N
        #L = list(max(positions.T[i])*2 for i in (0,1,2))
        #s.configuration.box = [L[0], L[1], L[2], 0, 0, 0]
        f.append(s)
    end = time.time()
    print('Ran debubble in ', end-start, 'for an image with shape ', reskel.shape)

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
        print('Saved ', operation, ' in ', end-start, ' for a graph with ', len(G.nodes()), ' nodes')
    
    avg_indices = igraph_avg_indices(I)
    
    with open(directory+'/graphwise.csv', 'w') as f:
        for key in avg_indices:
            f.write("%s,%s\n"%(key,avg_indices[key]))
    



def benchmark(gsd_name,skel_name):
    start = time.time()
#Generate NetworkX type graph object
    G = gsd_to_G(gsd_name)
    G=sub_G(G)
    end = time.time()
    print("gsd_to_G() in",end-start)

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

#Binarizes stack of experimental images using a set of image processing parameters in options_json.
def ExpProcess(directory, options_json=None):
    
    if options_json is None:
        options_json = directory + '/img_options.json'
    
    with open(options_json) as f:
        options_dict = json.load(f)
        
    #Reset write directory
    try:
        shutil.rmtree(directory+'/'+'Binarized')
    except FileNotFoundError:
        pass
    os.mkdir(directory+'/'+'Binarized')
    
    #Generate
    i=0    
    for name in sorted(os.listdir(directory)):
        if name.endswith('.tif')==False:
            pass
        else:
            img_exp = cv.imread(directory+'/'+name,cv.IMREAD_GRAYSCALE)
            if img_exp is None:
                raise TypeError('img_exp is None')
            _, img_bin, _ = process_image.binarize(img_exp, options_dict)
            plt.imsave(directory+'/'+'Binarized'+'/'+'slice'+str(i)+'.tiff', img_bin, cmap=cm.gray)
            i+=1

#Unusual case of writing binary stack to gsd without skeletonizing. Effective for creating direct 3d reconstruction.
#Takes directory where stack is located, and a gsd write filename
#NOTE THIS CROPPING IMPLEMENTATION USES FRACTIONAL VALUES
def stack_to_gsd(stack_directory, gsd_name, crop=False, debubble=False):
    start = time.time()
    img_bin=[]

    #Initilise i such that it starts at the lowest number belonging to the images in the stack_directory
    #First require boolean mask to filter out non image files
    olist = np.asarray(sorted(os.listdir(stack_directory)))
    mask = list(Q_img(olist[i]) for i in range(len(olist)))
    name = sorted(olist[mask])[0] #First name
    i = int(os.path.splitext(name)[0][5:]) #Strip file type and 'slice' then convert to int
    #Generate 3d array from stack
    for name in sorted(os.listdir(stack_directory)):
        if Q_img(name):
            img_slice = cv.imread(stack_directory+'/slice'+str(i)+'.tiff',cv.IMREAD_GRAYSCALE)
            img_bin.append(img_slice)
            i=i+1
        else:
            pass

    positions = np.asarray(np.where(np.asarray(img_bin) != 0)).T
    dims = np.asarray(list(max(positions.T[i]) for i in (0,1,2)))
    if crop != False:
        from numpy import logical_and as a
        crop_abs = (dims[0]*crop[0], dims[0]*crop[1], dims[1]*crop[2], dims[1]*crop[3], dims[2]*crop[4], dims[2]*crop[5])
        p=positions.T
        positions = p.T[a(a(a(a(a(p[0]>crop_abs[0],p[0]<crop_abs[1]),p[1]>crop_abs[2]),p[1]<crop_abs[3]),p[2]>crop_abs[4]),p[2]<crop_abs[5])]

    with gsd.hoomd.open(name=gsd_name, mode='wb') as f:
        s = gsd.hoomd.Snapshot()
        s.particles.N = len(positions)
        s.particles.position = positions
        s.particles.types = ['A']
        s.particles.typeid = ['0']*s.particles.N
        f.append(s)
    end = time.time()
    print('Ran stack_to_gsd() in ', end-start, 'for gsd with ', len(positions), 'particles')

def add_weights(G, stack_directory, crop=None, weight_type=None):
    start = time.time()
    img_bin = stack_to_canvas(stack_directory, crop)
    end = time.time()
    print('Loaded img in ', end-start)
    start = time.time()
    for (s, e) in G.edges():
        ge = G[s][e]['pts']
        pix_width, wt = GetWeights_3d.assignweights(ge, img_bin, weight_type=weight_type)
        G[s][e]['pixel width'] = pix_width
        G[s][e]['weight'] = wt
    end = time.time()
    print('Added weights to a graph  with ', len(G.nodes()), 'nodes in ', end-start)
    
    return G

def stack_analysis(stack_directory, suffix, ANC=False, crop=False):
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
def voltage_distribution(stack_directory, gsd_name, plane, boundary1, boundary2, graph=None, crop=None, I_dim=1):#, R_dim=1):
    print('stack_directory ', stack_directory)
    print('gsd_name ', gsd_name)
    print('plane', plane)
    print('boundary1 ', boundary1)
    print('boundarry2 ', boundary2)
    print('crop', crop)
    
    if graph is None:
        start = time.time()
        G = gsd_to_G(gsd_name, crop=crop)
        end = time.time()
        print('Ran gsd_to_G() in', end-start)    
    else:
        G = graph
    
    G = sub_G(G)
    G = add_weights(G, stack_directory, crop, weight_type='Resistance')
    G = ig.Graph.from_networkx(G)  
    weight_array = np.asarray(G.es['weight']).astype(float)
    weight_array = weight_array[~np.isnan(weight_array)]
    weight_avg =np.mean(weight_array)
  

#Add source and sink nodes:
    source_id = max(G.vs)['_nx_name'] + 1
    sink_id = source_id + 1
    G.add_vertices(2)
#Add coords for plotting
    positions = []
    for i in range(G.vcount()):
        if G.vs[i]['o'] is None:
            pass
        else:
            positions.append(G.vs[i]['o'].ravel())
    positions = np.concatenate(np.asarray(positions)).reshape((len(positions),3))
    dims = list(max(positions.T[i]) for i in (0,1,2))
    #dims = list(max(np.stack(list(G.vs[i]['o'] for i in range(G.vcount()))).T[j]) for j in (0,1,2)) 
    #mins = list(min(np.asarray(list(G.vs[i]['o'] for i in range(G.vcount())), dtype=object).T[j]) for j in (0,1,2))
    #print(np.asarray(list(G.vs[i]['o'] for i in range(G.vcount()))).T)
    print('Graph has max ', dims)
    axes = np.array([0,1,2])
    i,j = axes[axes!=plane]
    plane_centre1 = np.array([0,0,0])
    delta = np.array([0,0,0])
    delta[plane] = 10 #Arbitrary. Standardize?
    plane_centre1[i] = dims[i]/2
    plane_centre1[j] = dims[j]/2
    plane_centre2 = np.copy(plane_centre1)
    plane_centre2[plane] = dims[plane]
    source_coord = plane_centre1 - delta 
    sink_coord = plane_centre2 + delta
    print('source coord is ', source_coord)
    print('sink coord is ', sink_coord)
    G.vs[source_id]['o'] = source_coord
    G.vs[sink_id]['o'] = sink_coord

#Connect nodes on a given boundary to the external current nodes
    print('Before connecting external nodes, G has vcount ', G.vcount())
    for node in G.vs:
        if node['o'][plane] > boundary1[0] and node['o'][plane] < boundary1[1]:
            G.add_edges([(node['_nx_name'], source_id)])
            G.es[G.get_eid(node['_nx_name'],source_id)]['weight'] = weight_avg
            G.es[G.get_eid(node['_nx_name'],source_id)]['pts'] = connector(source_coord,node['o'])
        if node['o'][plane] > boundary2[0] and node['o'][plane] < boundary2[1]:
            G.add_edges([(node['_nx_name'], sink_id)])
            G.es[G.get_eid(node['_nx_name'],sink_id)]['weight'] = weight_avg 
            G.es[G.get_eid(node['_nx_name'],sink_id)]['pts'] = connector(sink_coord,node['o'])

#Write skeleton connected to external node
    print(G.is_connected(), ' connected')
    print('After connecting external nodes, G has vcount ', G.vcount())
    connected_name = os.path.split(gsd_name)[0] + '/connected_' + os.path.split(gsd_name)[1] 
    G_to_gsd(G, connected_name)

    L = weighted_Laplacian(G)
    I = np.zeros(sink_id+1)
    print(I.shape,'I')
    print(L.shape, 'L')
    I[source_id] = I_dim
    I[sink_id] = -I_dim
    np.save('L.npy',L)
    np.save('I.npy',I)
    VC =np.linalg.solve(L,I)
    np.save('VC.npy',VC)
    print(VC)
    return VC,G

#Labelling function which takes an attribute calculating function and its relevant parameters (usually gsd, img_bin and, optionally, crop)
#The labelling function calls the attribute calculating function so that the graph and its nodes' attributes are returned
#The labelling funciton appends the attribute to the graph and rewrites the gsd
#Note that all attribute calculating functions must return the attribute tensor and the graph which is to be labelled
#Note that the gsd_name specified in Node_labelling is the name under which to save the labelled graph; the gsd_name given in *args is the file in which the unlabelled graph should be extracted from
def Node_labelling(AttrCalcFunc, attribute_name, prefix, *args, **kwargs):

    #positions = gsd.hoomd.open(name=gsd_name, mode='rb')[0].particles.position
    start = time.time()
    attribute,G = AttrCalcFunc(*args, **kwargs)
    print(attribute)
    end = time.time()
    #G = sub_G(G)
    #G = ig.Graph.from_networkx(G) 
    save_name = os.path.split(prefix)[0] + '/'+attribute_name + os.path.split(prefix)[1]
    f = gsd.hoomd.open(name=save_name, mode='wb')
    node_positions = np.asarray(list(G.vs()[i]['o'] for i in range(G.vcount())))
    #node_positions = shift(node_positions).astype(int)
    positions = node_positions
    for edge in G.es():
        positions=np.vstack((positions,edge['pts']))
    positions = np.unique(positions, axis=0)
    #positions = shift(positions).astype(int)
    
    node_origin_shift =(np.full((np.shape(node_positions)[0],3),[np.max(positions.T[0])/2,np.max(positions.T[1])/2,np.max(positions.T[2])/2])) 
    position_origin_shift = (np.full((np.shape(positions)[0],3),[np.max(positions.T[0])/2,np.max(positions.T[1])/2,np.max(positions.T[2])/2]))
    node_positions = node_positions - node_origin_shift
    positions = positions - position_origin_shift


    
    print('final positions are ', positions)
    print('node positions are ', node_positions)
    
    s = gsd.hoomd.Snapshot()
    N = len(positions)
    s.particles.N = N
    s.particles.position = positions
    s.particles.types = ['Edge', 'Node']
    s.particles.typeid = [0]*N
    L = list(max(positions.T[i])*2 for i in (0,1,2))
    s.configuration.box = [L[0], L[1], L[2], 0, 0, 0]
    s.log['particles/'+attribute_name] = [np.NaN]*N
    start = time.time()

    print('positions has len ', len(positions))
    print('ig node_positions has len ', len(node_positions))
    print('attribute has len ', len(attribute))
    print('log has len ', len(s.log['particles/'+attribute_name]))
    j=0
    print(attribute[2])
    for i,particle in enumerate(positions):
        node_id = np.where(np.all(positions[i] == node_positions, axis=1) == True)[0]
        if len(node_id) == 0: 
            continue
        else:
            s.log['particles/'+attribute_name][i] = attribute[node_id[0]]
            s.particles.typeid[i] = 1
            j+=1
    


    #    for j,node in enumerate(node_positions):
    #        if sum(node == particle) == 3:
    #            s.log['particles/'+attribute_name][i] = attribute[j]
    #            s.particles.typeid[i] = 1
    

    #a,b,c=np.intersect1d(positions, node_positions, return_indices=True)
    #print(a)
    #print(b)
    #print(c)

    #print('node indices has len ', len(node_indices))
    #for i,index in enumerate(node_indices):
    #    s.log['particles/'+attribute_name][index] = attribute[i]
    #    s.particles.typeid[index] = 1
    


    f.append(s)
 
