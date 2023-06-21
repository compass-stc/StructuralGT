from StructuralGTEdits import util, base, convert
import pandas as pd
import numpy as np
import freud
import igraph as ig
import os
from skimage.measure import regionprops, label
import gsd.hoomd



class InteractionNetwork(util.Network):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def G_u(self, crop, edge_weight='Length', node_weight='Volume',
            _dict=dict(num_neighbors=4, exclude_ii=True)):

        self.set_img_bin(crop)
        print('img_bin has been set')
        crop=[crop[4],crop[5],crop[0],crop[1],crop[2],crop[3]]

        G = ig.Graph()
        label_img = label(self.img_bin)
        regions = regionprops(label_img)

        node_weights, points = [], []
        for region in regions:
            points.append(region.centroid)
            node_weights.append(region.area)
        G.add_vertices(len(regions))
        G.vs['Weight'] = node_weights
        G.vs["o"] = points

        points = np.array(points)
        # TOOD: Replace with shape
        self.box = [(crop[1]-crop[0])*4,
                    (crop[3]-crop[2])*4,
                    (crop[5]-crop[4])*4,0,0,0]
        box = freud.box.Box(self.box[0], self.box[1], self.box[2])
        aq = freud.locality.AABBQuery(box, points)

        nlist = []

        edge_weights = []
        nlist = aq.query(points, _dict).toNeighborList()
        G.add_edges(nlist)
        for bond in aq.query(points, _dict):
            edge_weights.append(bond[2])
        G.es['Weight'] = edge_weights

        self.Gr = G

        self.nlist = nlist
        self.points = points

    def to_gsd(self, filename='skel.gsd', label='Degree', mode='r+'):
        
        if filename[0] == "/":
            save_name = filename
        else:
            save_name = self.stack_dir + "/" + filename
        
        if mode == "r+" and os.path.exists(save_name):
            _mode = "r+"
        else:
            _mode = "w"

        f = gsd.hoomd.open(name=save_name, mode=_mode)
        self.labelled_name = save_name

        node_positions = np.asarray(
            list(self.Gr.vs()[i]["o"] for i in range(self.Gr.vcount()))
        )
        
        edge_positions = np.array([[0,0,0]], dtype=float)
        for bond in self.nlist:
            edge_positions = np.append(edge_positions, 
                    base.connector(self.points[bond[0]], self.points[bond[1]]), axis=0)

        positions = np.append(edge_positions, node_positions, axis=0)
        N = len(positions)
        s = gsd.hoomd.Frame()
        s.particles.N = N
        s.particles.position = positions
        s.particles.types = ["Edge", "Node"]
        s.particles.typeid = [0] * N
        s.log["particles/" + label] = [np.NaN] * N
        s.configuration.box = self.box
        
        matrix = self.Gr.get_adjacency_sparse(attribute='Weight')
        rows, columns = matrix.nonzero()
        values = matrix.data
        
        #rows, columns, values = convert.to_dense(
        #    np.array(self.Gr.get_adjacency(attribute='Weight').data, dtype=np.single)
        #)
        s.log["Adj_rows"] = rows
        s.log["Adj_cols"] = columns
        s.log["Adj_values"] = values
        
        j = 0
        for i, particle in enumerate(positions):
            node_id = np.where(np.all(positions[i] == node_positions, axis=1) == True)[
                0
            ]
            if len(node_id) == 0:
                continue
            else:
                #s.log["particles/" + label][i] = attribute[node_id[0]]
                s.particles.typeid[i] = 1
                j += 1

        f.append(s)

 


