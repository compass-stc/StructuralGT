# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.



import freud
import gsd.hoomd
import igraph as ig
import numpy as np
from collections.abc import Sequence


class Regions:
    def __init__(self, partition, box):
        if partition == 0:
            self.regions = [
                [
                    (-box[0] / 2, box[0] / 2),
                    (-box[1] / 2, box[1] / 2),
                    (-box[2] / 2, box[2] / 2),
                ]
            ]
        elif partition == 1:
            self.regions = [
                [(-box[0] / 2, 0), (-box[1] / 2, 0), (-box[2] / 2, 0)],
                [(-box[0] / 2, 0), (-box[1] / 2, 0), (0, box[2] / 2)],
                [(-box[0] / 2, 0), (0, box[1] / 2), (-box[2] / 2, 0)],
                [(-box[0] / 2, 0), (0, box[1] / 2), (0, box[2] / 2)],
                [(0, box[0] / 2), (-box[1] / 2, 0), (-box[2] / 2, 0)],
                [(0, box[0] / 2), (-box[1] / 2, 0), (0, box[2] / 2)],
                [(0, box[0] / 2), (0, box[1] / 2), (-box[2] / 2, 0)],
                [(0, box[0] / 2), (0, box[1] / 2), (0, box[2] / 2)],
            ]

    def inregion(self, region, p):
        mask = (
            np.array(p.T[0] > region[0][0])
            & np.array(p.T[0] < region[0][1])
            & np.array(p.T[1] > region[1][0])
            & np.array(p.T[1] < region[1][1])
            & np.array(p.T[2] > region[2][0])
            & np.array(p.T[2] < region[2][1])
        )

        return p[mask]


class ParticleNetwork(Sequence):
    def __init__(self, trajectory, cutoff, partition=0, periodic=False):
        self.traj = gsd.hoomd.open(trajectory)
        self.cutoff = cutoff
        self.periodic = periodic
        self.partition = partition

        self.regions = Regions(partition, self.traj[0].configuration.box)

    def __getitem__(self, key):
        self._graph_list = []
        if isinstance(key, int):
            _iter = [self.traj[key]]
        else:
            _iter = self.traj[key]
        for frame in _iter:
            _first = True
            for region in self.regions.regions:
                positions = self.regions.inregion(region,
                                                  frame.particles.position)
                box = frame.configuration.box * {False: 2, True: 1}[
                        self.periodic]
                aq = freud.locality.AABBQuery(box, positions)
                nlist = aq.query(
                    positions,
                    {"r_max": self.cutoff, "exclude_ii": True},
                ).toNeighborList()
                nlist.filter(nlist.query_point_indices < nlist.point_indices)
                if _first:
                    _graph = ig.Graph.TupleList(nlist[:], directed=False)
                    _first = False
                else:
                    nlist = nlist[:] + _graph.vcount()
                    __graph = ig.Graph.TupleList(nlist[:], directed=False)
                    _graph = ig.operators.union([_graph, __graph])

            self._graph_list.append(_graph)

        return self._graph_list

    def __len__(self):
        return len(self._graph_list)
