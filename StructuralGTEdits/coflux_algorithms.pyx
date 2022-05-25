import numpy as np
import igraph as ig
import network

def create_graph():
    N = network.ResistiveNetwork('TestData/AgNWN_10um')
    N.binarize()
    N.stack_to_gsd(crop=[400, 800, 200, 600])
    N.G_u(weight_type=['Resistance','FixedWidthConductance'], R_j=0)
    N.potential_distribution(0, [0,20], [719,719-20], R_j=0, rho_dim=0.69)
    N.Node_labelling(N.P, 'P', 'test1.gsd')

    return N
   

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
                Ax_term  = Ax_term  + weight*(((float(G.vs[hop_s]['o'][0])-float(G.vs[hop_t]['o'][0])))**2)
                Ay_term  = Ay_term  + weight*(((float(G.vs[hop_s]['o'][1])-float(G.vs[hop_t]['o'][1])))**2)
                Axy_term = Axy_term + weight*(((float(G.vs[hop_s]['o'][1])-float(G.vs[hop_t]['o'][1])))*((float(G.vs[hop_s]['o'][0])-float(G.vs[hop_t]['o'][0]))))
            Ax  = Ax  + (Ax_term)
            Ay  = Ay  + (Ay_term)
            Axy = Axy + (Axy_term)
            A = np.array([[Ax,Axy,0],[Axy,Ay,0],[0,0,0]])
    return A

def gyration_moments_4(G, sampling = 1, weighted=True):  
    cdef float Ax = 0
    cdef float Ay = 0
    cdef float Axy = 0
    
    cdef float Ax_term  = 0
    cdef float Ay_term  = 0
    cdef float Axy_term = 0
    
    node_count = np.asarray(list(range(G.vcount())),dtype=int)
    mask = np.random.rand(G.vcount()) > (1-sampling)
    trimmed_node_count = node_count[mask]
    for i in trimmed_node_count:
        for j in trimmed_node_count:
            
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
                Ax_term  = Ax_term  + weight*(((int(G.vs[hop_s]['o'][0])-int(G.vs[hop_t]['o'][0])))**2)
                Ay_term  = Ay_term  + weight*(((int(G.vs[hop_s]['o'][1])-int(G.vs[hop_t]['o'][1])))**2)
                Axy_term = Axy_term + weight*(((int(G.vs[hop_s]['o'][1])-int(G.vs[hop_t]['o'][1])))*((int(G.vs[hop_s]['o'][0])-int(G.vs[hop_t]['o'][0]))))
            Ax  = Ax  + (Ax_term)
            Ay  = Ay  + (Ay_term)
            Axy = Axy + (Axy_term)
            A = np.array([[Ax,Axy,0],[Axy,Ay,0],[0,0,0]])
    return A



def case_one():
    N = create_graph()
    gyration_moments_3(N.Gr, sampling = 0.01, weighted=False)
