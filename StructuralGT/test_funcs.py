import numpy as np
import sknw
import networkx as nx

def canvas_to_G(name):

    canvas = np.load(name)
    G = sknw.build_sknw(canvas.astype(int))


def gsd_to_pos(gsd_name, crop=False, parallelize = False):
    import gsd.hoomd
    frame = gsd.hoomd.open(name=gsd_name+'.gsd', mode='rb')[0]
    positions = frame.particles.position.astype(int)
    
    if crop != False:
        print('crop')
        canvas = np.zeros(list((max(positions.T[i])+1) for i in (0,1,2)))
        canvas[tuple(list(positions.T))] = 1
        np.shape(canvas)
        canvas = canvas[crop[0]:crop[1],
                          crop[2]:crop[3],
                          crop[4]:crop[5]]
       
        positions = np.asarray(np.where(canvas==1)).T

    if parallelize != False:
        canvas = canvas
        
    return positions

