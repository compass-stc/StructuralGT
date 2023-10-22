from StructuralGTEdits import util, base
import numpy as np
import freud
import igraph as ig
import os
from skimage.measure import regionprops, label
import gsd.hoomd

class InteractionNetwork(util.Network):
    """Class for extracting bond networks from particle images. In this class,
    nodes are particles, and edges connect neighbouring particles.
    Neighbours are found using freudCITE.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_graph(self, crop, edge_weight='Length', node_weight='Volume',
            _dict=dict(num_neighbors=4, exclude_ii=True)):
        """Calculates a neighbour list and sets the resulting 
        :class:`igraph.Graph` object as an attribute. 

        Args:
            crop (list)
                The x, y and (optionally) z coordinates of the cuboid/
                rectangle which encloses the :class:`Network` region of
                interest.
            edge_weight (optional, str):
                How to weight the edges.
            node_weight (optional, str):
                How to weight the nodes.
            _dict (optional, dict):
                Dictionary of neighbour finding arguements to pass to freud's
                :meth:`query` method.
        """

        self.set_img_bin(crop)
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
        """Writes .gsd file from :attr:`Gr` attribute.

        Args:
            filename (optional, str):
                Filename to write to. Defaults to skel.gsd
            label (optional, str):
                Node attribute to write to gsd file
            mode (optional, str):
                The writing mode.
        """
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
