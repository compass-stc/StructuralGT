# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.


import freud
import gsd.hoomd
import igraph as ig
import numpy as np

from . import base



class PointNetwork:
    """Class for creating graphs from point cloud data.

    Args:
        positions (:class:`numpy.ndarray`):
            The coordinates of the points in the point cloud.
        cutoff (float):
            The cutoff distance for creating edges between points.
        periodic (bool):
            Whether to use periodic boundary conditions. Default is False.
    """

    def __init__(self, positions, cutoff, periodic=False):
        self.cutoff = cutoff
        self.periodic = periodic
        self.dim = positions.shape[1]

        for dim in range(self.dim):
            positions[:, dim] = (positions[:, dim] - positions[:, dim].min())
        L = list(max(positions.T[i]) for i in range(self.dim))
        positions, _ = base.shift(positions, _shift=(L[0] / 2, L[1] / 2, L[2] / 2))
        box = [L[0], L[1], L[2], 0, 0, 0]

        self.positions = positions
        self.box = box

        aq = freud.locality.AABBQuery(self.box, positions)
        nlist = aq.query(
            positions,
            {"r_max": self.cutoff, "exclude_ii": True},
        ).toNeighborList()
        nlist.filter(nlist.query_point_indices < nlist.point_indices)
        self.graph = ig.Graph()
        self.graph.add_vertices(len(positions))
        # Create edges based on the neighbor list
        for i in range(len(nlist.point_indices)):
            self.graph.add_edge(
                nlist.point_indices[i],
                nlist.query_point_indices[i],
            )

    def point_to_skel(self, filename='skel.gsd'):
        """Method saves a new :code:`.gsd` with the graph
        structure.

        Args:
            filename (str):
               The filename to save the :code:`.gsd` file to.
        """

        N = self.graph.vcount()
        bonds = np.array(self.graph.get_edgelist())
        bond_types = ['0']

        snapshot = gsd.hoomd.Frame()
        snapshot.particles.N = N
        snapshot.particles.types = ['A']
        snapshot.particles.position = self.positions
        snapshot.particles.typeid = [0] * N
        snapshot.particles.bond_types = bond_types
        snapshot.particles.bonds = bonds
        snapshot.configuration.box = self.box
        snapshot.bonds.N = len(bonds)
        snapshot.bonds.group = bonds
        snapshot.bonds.types = bond_types
        snapshot.bonds.typeid = np.zeros(len(bonds), dtype=np.uint32)

        with gsd.hoomd.open(name=filename, mode='w') as f:
            f.append(snapshot)

        self.filename = filename

    def node_labelling(self, attributes, labels, filename='labelled.gsd'):
        """Method saves a new :code:`.gsd` which labels the :attr:`graph`
        attribute with the given node attribute values.

        Args:
            attribute (:class:`numpy.ndarray`):
                An array of attribute values in ascending order of node id.
            label (str):
                The label to give the attribute in the file.
        """

        if not isinstance(labels, list):
            labels = [labels,]
            attributes = [attributes,]

        with gsd.hoomd.open(name=self.filename, mode='r') as f:
            s = f[0]
            for attribute, label in zip(attributes, labels):
                if len(attribute) != s.particles.N:
                    raise ValueError(
                            f"Attribute length {len(attribute)} "
                            "does not match number of particles "
                            "{s.particles.N}."
                            )
                s.log["particles/" + label] = attribute

        with gsd.hoomd.open(name=filename, mode='w') as f_mod:
            f_mod.append(s)
