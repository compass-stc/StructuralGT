# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import os

import numpy as np

from StructuralGT import base
from StructuralGT.util import _Compute


class Electronic(_Compute):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compute(self, network, R_j, axis, boundary_conditions, source=-1,
                sink=-2):
        """
        Args:
            source (int, optional):
                Source node id.
            sink (int, optional):
                Sink node id.
        """
        self.source = source
        self.sink = sink
        network.R_j = R_j
        boundary1 = boundary_conditions[0]
        boundary2 = boundary_conditions[1]
        network.graph_connected = network.graph
        if network.R_j != "infinity":
            weight_array = np.asarray(
                    network.graph.es["Conductance"]).astype(float)
            weight_array = weight_array[~np.isnan(weight_array)]
            # self.edge_weights = weight_array
            weight_avg = np.mean(weight_array)
        else:
            network.graph_connected.es["Conductance"] = \
                    np.ones(network.graph.ecount())
            weight_avg = 1

        # Add source and sink nodes:
        source_id = max(network.graph_connected.vs).index + 1
        sink_id = source_id + 1
        network.graph_connected.add_vertices(2)

        print("Graph has shape ", network.shape)
        axes = np.array([0, 1, 2])[0: network.dim]
        indices = axes[axes != axis]
        axis_centre1 = np.zeros(network.dim, dtype=int)
        delta = np.zeros(network.dim, dtype=int)
        delta[axis] = 10  # Arbitrary. Standardize?
        for i in indices:
            axis_centre1[i] = network.shape[i] / 2
        axis_centre2 = np.copy(axis_centre1)
        axis_centre2[axis] = network.shape[axis]
        source_coord = axis_centre1 - delta
        sink_coord = axis_centre2 + delta
        print("Source coordinate is ", source_coord)
        print("Sink coordinate is ", sink_coord)
        network.graph_connected.vs[source_id]["o"] = source_coord
        network.graph_connected.vs[sink_id]["o"] = sink_coord
        network.graph_connected.vs[source_id]["pts"] = source_coord
        network.graph_connected.vs[sink_id]["pts"] = sink_coord

        for node in network.graph_connected.vs:
            if (node["o"][axis] >= boundary1[0]
                    and node["o"][axis] <= boundary1[1]):
                network.graph_connected.add_edges([(node.index, source_id)])
                network.graph_connected.es[
                    network.graph_connected.get_eid(node.index, source_id)
                ]["Conductance"] = weight_avg
                network.graph_connected.es[
                    network.graph_connected.get_eid(node.index, source_id)
                ]["pts"] = base.connector(source_coord, node["o"])
            if (node["o"][axis] >= boundary2[0]
                    and node["o"][axis] <= boundary2[1]):
                network.graph_connected.add_edges([(node.index, sink_id)])
                network.graph_connected.es[
                    network.graph_connected.get_eid(node.index, sink_id)
                ]["Conductance"] = weight_avg
                network.graph_connected.es[
                    network.graph_connected.get_eid(node.index, sink_id)
                ]["pts"] = base.connector(sink_coord, node["o"])

        # Write skeleton connected to external node
        connected_name = (
            os.path.split(network.gsd_name)[0]
            + "/connected_"
            + os.path.split(network.gsd_name)[1]
        )
        base.G_to_gsd(network.graph_connected, connected_name)

        if network.R_j == "infinity":
            network.L = np.asarray(network.graph.laplacian())
        else:
            network.L = np.asarray(network.graph.laplacian(
                weights="Conductance"))

        F = np.zeros(sink_id + 1)
        F[source_id] = 1
        F[sink_id] = -1

        Q = np.linalg.pinv(network.L, hermitian=True)
        P = np.matmul(Q, F)

        self._P = P
        self._Q = Q

    @_Compute._computed_property
    def effective_resistance(self):
        """Returns the effective resistance between the source and sink,
        according to the method of :cite:`Klein1993`.

        """

        return (
            self.Q[self.source, self.source]
            + self.Q[self.sink, self.sink]
            - 2 * self.Q[self.source, self.sink]
        )

    @_Compute._computed_property
    def P(self):
        """:class:`np.ndarray`: The vector of potentials at each node."""
        return self._P

    @_Compute._computed_property
    def Q(self):
        """:class:`np.ndarray`: pseudoinverse of the graph Laplacian,
        weighted by conductance. This property is immediately available if
        :meth:`potential_distribution` has been called. Otherwise it may be
        calculated by inverting the graph Laplacian, accessed via the
        :meth:`laplacian` method of the :attr:`graph` attribute."""

        return self._Q
