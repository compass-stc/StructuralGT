import cv2 as cv 
import numpy as np 
import gsd.hoomd 
import skel_ID_3d
import networkx as nx
import sknw


##Function which savs list of coordinates as a gsd, with node points (as defined by hit or miss) optionally labelled
def create_frame(skel, aspect=(1,1,1), branch=None, end=None): 
    s = gsd.hoomd.Snapshot() 
    coords_list = [] 
    for coords in (skel, branch, end): 
        for i in (0,1,2): 
            coords[i] = coords[i]*aspect[i] 
        coords_list.append(coords) 
 
    N_skel, N_branch, N_end = list(len(coords_list[i]) for i in np.arange(len(coords_list))) 
         
    with gsd.hoomd.open(name=name+'.gsd', mode='wb') as f: 
        s.particles.N = sum((N_skel, N_branch, N_end)) 
        s.particles.position = np.concatenate((coords_list[0],coords_list[1],coords_list[2])) 
        s.particles.types = ['S','B','E'] 
        s.particles.typeid = ['0']*N_skel + ['1']*N_branch + ['2']*N_end 
        f.append(s) 

import os

try:
    os.remove('preskel.npy')
    os.remove('skelcomplete.npy')
    os.remove('framewritten.npy')
    os.remove('canvasinitialised.npy')
    os.remove('graphbuilt.npy')
except:
    FileExistsError

params = dict(directory ='ANF2_50')
np.save('preskel.npy',[0])
skel, branch, end = skel_ID_3d.make_skel(params, (1,1,1), 0,0,0,0)
np.save('skelcomplete.npy',[0])
create_frame(skel, branch=branch, end=end)
#np.save('framewritten.npy',[0])
#canvas = np.zeros((max(skel.T[0])+1,max(skel.T[1])+1,max(skel.T[2])+1))
#np.save('canvasinitialised.npy',[0])
#G = sknw.build_sknw(canvas)
#np.save('grapbuilt.npy',[0])
#print(G.edges())
#nx.write_gexf(G, "full.gexf")
#nx.write_edgelist(G, "full.edgelist")
#nx.write_graphml(G, "full.graphml")                         
