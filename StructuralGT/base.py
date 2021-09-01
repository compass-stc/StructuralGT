import numpy as np
import sknw
import networkx as nx
import gsd.hoomd
def canvas_to_G(name):

    canvas = np.load(name)
    G = sknw.build_sknw(canvas.astype(int))

def shift(points):
    shift=(np.full((np.shape(points)[0],3),[np.min(points.T[0]),np.min(points.T[1]),np.min(points.T[2])]))
    points = points - shift
    return points

#Functions returns list of position from a given gsd file. Optionally, it may return a list of positions that only fall within a given set of dimensions, effectively cropping the domain. TODO replace cropping with array masking method
def gsd_to_pos(gsd_name, crop=False):
    frame = gsd.hoomd.open(name=gsd_name, mode='rb')[0]
    positions = frame.particles.position.astype(int)
    
    if crop != False:
        print('crop')
        canvas = np.zeros(list((max(positions.T[i])+1) for i in (0,1,2)))
        canvas[tuple(list(positions.T))] = 1
        canvas = canvas[crop[0]:crop[1],
                          crop[2]:crop[3],
                          crop[4]:crop[5]]
       
        positions = np.asarray(np.where(canvas==1)).T

    return positions

#Function takes gsd rendering of a skeleton and returns the list of nodes and edges, as calculated by sknw. Optionally, it may crop. sub=True will reduce the returned graph to the largest connected induced subgraph, resetting node numbers to consecutive integers, starting from 0.
def gsd_to_G(gsd_name, crop=False, sub=False):
    frame = gsd.hoomd.open(name=gsd_name, mode='rb')[0]
    positions = frame.particles.position.astype(int)

    if crop != False:
        from numpy import logical_and as a
        p=positions.T
        positions = p.T[a(a(a(a(a(p[0]>crop[0],p[0]<crop[1]),p[1]>crop[2]),p[1]<crop[3]),p[2]>crop[4]),p[2]<crop[5])]

    canvas = np.zeros(list((max(positions.T[i])+1) for i in (0,1,2)))
    canvas[tuple(list(positions.T))] = 1
    canvas = canvas.astype(int)
    G = sknw.build_sknw(canvas)

    if sub:
        G_sub  = G.subgraph(max(nx.connected_components(G), key=len).copy())
#        G = nx.relabel.convert_node_labels_to_integers(G_sub)
    
    return G
    
#Function reads, crops and rewrites gsd file. TODO write branch and endpoint data to new gsd file (currently this info is lost).
def gsd_crop(gsd_name, save_name, crop):
    frame = gsd.hoomd.open(name=gsd_name, mode='rb')[0]
    positions = frame.particles.position.astype(int)

    from numpy import logical_and as a
    p=positions.T
    positions = p.T[a(a(a(a(a(p[0]>crop[0],p[0]<crop[1]),p[1]>crop[2]),p[1]<crop[3]),p[2]>crop[4]),p[2]<crop[5])]
    positions_T = positions.T
    positions_T[0] = positions_T[0]/2
    positions = positions_T.T
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

    import time
    
    G = gsd_to_G(gsd_name)
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


#Function generates largest connected induced subgraph from graph defined by given name of edge and list .txt. files. Node and edge numbers are reset such that they are consecutive integers, starting from 0
def sub_G(nodes_file_name, edges_file_name):
    G = nx.Graph()
    
    edges = np.loadtxt(edges_file_name).astype(int)
    nodes = np.loadtxt(nodes_file_name).astype(int)
    
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    G_sub  = G.subgraph(max(nx.connected_components(G), key=len).copy())

    G = nx.relabel.convert_node_labels_to_integers(G_sub)
    
    return G

#Function takes a gsd name, generates a graph with gsd_to_G() and resaves a new .gsd file which has some nodewise indices saved to the file
def G_labelling(gsd_name):
    from networkx.algorithms.centrality import betweenness_centrality, closeness_centrality
    G = gsd_to_G(gsd_name)
    
    operations = [nx.degree, nx.clustering, betweenness_centrality, closeness_centrality]
    names = ['Degree', 'Clustering', 'Betweenness_Centrality', 'Closeness_Centrality']

    f = gsd.hoomd.open(name='labelled'+gsd_name, mode='wb')

    node_positions = np.asarray(list(G.nodes()[i]['o'] for i in np.arange(len(G.nodes()))))
    positions = gsd.hoomd.open(name=gsd_name, mode='rb')[0].particles.position

    node_positions = shift(node_positions)
    positions = shift(positions)
    
    node_origin_shift =(np.full((np.shape(node_positions)[0],3),[np.max(positions.T[0])/2,np.max(positions.T[1])/2,np.max(positions.T[2])/2])) 
    position_origin_shift = (np.full((np.shape(positions)[0],3),[np.max(positions.T[0])/2,np.max(positions.T[1])/2,np.max(positions.T[2])/2]))

    node_positions = node_positions - node_origin_shift
    positions = positions - position_origin_shift

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
        index_list = operation(G)
    
        for i,particle in enumerate(positions):
            for j,node in enumerate(node_positions):
                if sum(node == particle) == 3:
                    s.log['particles/'+name][i] = index_list[j]
                    s.particles.typeid[i] = 1

    f.append(s)
    
    

