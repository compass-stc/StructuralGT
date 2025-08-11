# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import copy

import numpy as np
from StructuralGT.util import _Compute
import StructuralGT

if StructuralGT.__C_FLAG__ is False:
    raise RuntimeError("The betweenness module was never"
                       " compiled. Try resinstalling StructuralGT, ensuring"
                       " that the C_FLAG environment variable is not set to"
                       " False.")

from StructuralGT import (_boundary_betweenness_cast,
                          _random_boundary_betweenness_cast,
                          _vertex_boundary_betweenness_cast)

class NodeBetweenness(_Compute):
    """Module for conventional vertex betweenness."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compute(self, network):
        r"""Compute node betweenness centralities of the graph.

        Args:
            network (:class:`Network`):
                The :class:`Network` object.
        """

        self._node_betweenness = np.array(network.graph.betweenness()) / network.graph.vcount() / (network.graph.vcount() - 1 )

    @_Compute._computed_property
    def node_betweenness(self):
        r"""Node betweenness centrality.

        .. math::

           g(v) =\frac{1}{|N|(|N|-1)} \sum_{s\in N,t \in N} \frac{\sigma(s, t|v)}{\sigma(s, t)}

        where :math:`N` is the set of nodes, 
        :math:`\sigma(s, t)` is the number of shortest :math:`(s, t)` -paths,
        and :math:`\sigma(s, t|v)` is the number of those paths
        passing through node :math:`v` :cite:`Brandes2008`.
        """
        return self._node_betweenness
    
    @_Compute._computed_property
    def average_node_betweenness(self):
        r"""Average node betweenness centrality.

        .. math::

           \bar{g} = \frac{1}{|N|} \sum_{v\in N} g(v)
        """
        return np.mean(self._node_betweenness)

class NodeBoundaryBetweenness(_Compute):
    """A module for calculating different extension of the classical
    edge betweenness centrality measure. In particular, calculates
    betweennesses which include geometric features of the network via weights
    and boundary conditions.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compute(self, network, sources, targets):
        r"""Compute different edge betweenness centralities of the graph.

        Args:
            network (:class:`Network`):
                The :class:`Network` object.
            sources (list):
                The set of source nodes, :math:`S`.
            targets (list):
                The set of target nodes, :math:`T`.
        """

        num_edges = network.Gr.ecount()
        _copy = copy.deepcopy(network.Gr)

        if self.edge_weight is None:
            weights = np.ones(num_edges, dtype=np.double)
        else:
            weights = np.array(_copy.es[self.edge_weight], dtype=np.double)

        cast = _vertex_boundary_betweenness_cast.PyCast(_copy._raw_pointer())

        cast.vertex_boundary_betweenness_compute(
            np.array(sources, dtype=np.longlong),
            np.array(targets, dtype=np.longlong),
            num_edges,
            weights,
        )

        self._vertex_boundary_betweenness = cast.vertex_boundary_betweenness

    @_Compute._computed_property
    def vertex_boundary_betweenness(self):
        r"""Node betweenness centrality over a subset of nodes.
        Sometimes called betweenness subset.

        .. math::

           g_B(v) =\sum_{s\in S,t \in T} \frac{\sigma(s, t|e)}{\sigma(s, t)}

        where :math:`S` is the set of sources, :math:`T` is the set of targets,
        :math:`\sigma(s, t)` is the number of shortest :math:`(s, t)` -paths,
        and :math:`\sigma(s, t|e)` is the number of those paths
        passing through edge :math:`e` :cite:`Brandes2008`.
        """
        return self._vertex_boundary_betweenness


class BoundaryBetweenness(_Compute):
    """A module for calculating different extension of the classical
    edge betweenness centrality measure. In particular, calculates
    betweennesses which include geometric features of the network via weights
    and boundary conditions.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compute(self, network, sources, targets):
        r"""Compute different edge betweenness centralities of the graph.

        Args:
            network (:class:`Network`):
                The :class:`Network` object.
            sources (list):
                The set of source nodes, :math:`S`.
            targets (list):
                The set of target nodes, :math:`T`.
        """

        num_edges = network.Gr.ecount()
        _copy = copy.deepcopy(network.Gr)

        if self.edge_weight is None:
            weights = np.ones(num_edges, dtype=np.double)
        else:
            weights = np.array(_copy.es[self.edge_weight], dtype=np.double)

        cast = _boundary_betweenness_cast.PyCast(_copy._raw_pointer())

        cast.boundary_betweenness_compute(
            np.array(sources, dtype=np.longlong),
            np.array(targets, dtype=np.longlong),
            num_edges,
            weights,
        )

        self._boundary_betweenness = cast.boundary_betweenness

    @_Compute._computed_property
    def boundary_betweenness(self):
        r"""Edge betweenness centrality over a subset of nodes.
        Sometimes called betweenness subset.

        .. math::

           EBC_B(e) = \frac{1}{2|T|(|S|-1)} \sum_{s\in S,t \in T} \frac{\sigma(s, t|e)}{\sigma(s, t)}

        where :math:`S` is the set of sources, :math:`T` is the set of targets,
        :math:`\sigma(s, t)` is the number of shortest :math:`(s, t)` -paths,
        and :math:`\sigma(s, t|e)` is the number of those paths
        passing through edge :math:`e` :cite:`Brandes2008`.
        """
        return self._boundary_betweenness


class RandomBoundaryBetweenness(_Compute):
    """A module for calculating different extension of the classical
    edge betweenness centrality measure. In particular, calculates
    betweennesses which include geometric features of the network via weights
    and boundary conditions.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compute(self, network, sources, targets):
        r"""Compute different edge betweenness centralities of the graph.

        Args:
            network (:class:`Network`):
                The :class:`Network` object.
            sources (list):
                The set of source nodes, :math:`S`.
            targets (list):
                The set of target nodes, :math:`T`.
            weights (str, optional):
                The name of the edge attribute to be used in weighting the
                random walks. If omitted, an unweighted network is used.

        """
        _copy = copy.deepcopy(network.Gr)

        # Add ghost node and edges from targets to ghost
        _copy.add_vertex(1)
        for target in targets:
            _copy.add_edge(network.Gr.vcount() - 1, target)
        num_edges = _copy.ecount()

        # When passing weight vector, must add additional weights for edges
        # between targets and ghost node (added in cpp file)
        if self.edge_weight is None:
            weights = np.ones(num_edges, dtype=np.double)
        else:
            mean = np.mean(np.array(network.Gr.es[self.edge_weight]))

            weights = np.append(
                np.array(network.Gr.es[self.edge_weight], dtype=np.double),
                np.full(len(targets), mean, dtype=np.double),
            ).astype(np.double)
            assert len(weights) == _copy.ecount()
        cast = _random_boundary_betweenness_cast.PyCast(_copy._raw_pointer())

        cast.random_boundary_betweenness_compute(
            np.array(sources, dtype=np.longlong),
            np.array(targets, dtype=np.longlong),
            np.array(np.ones(len(sources)), dtype=np.longlong),
            num_edges,
            weights,
        )

        self._linear_betweenness = cast.linear_random_boundary_betweenness
        self._nonlinear_betweenness =\
            cast.nonlinear_random_boundary_betweenness

    @_Compute._computed_property
    def linear_betweenness(self):
        """A random walk betweenness that requires number of sources and
        targets to be equal for random walker balance (i.e. charge
        conservation).
        """
        return self._linear_betweenness

    @_Compute._computed_property
    def nonlinear_betweenness(self):
        """A random walk betweenness that does not requires number of sources
        and targets to be equal because a ghost sink node is added.
        """
        return self._nonlinear_betweenness
