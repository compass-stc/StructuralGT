# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import numpy as np

from StructuralGT.util import _Compute


class Size(_Compute):
    """Classical GT parameters. Calculates common proxies for network size.
    Edge weights are supported for the calculation of diameter.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compute(self, network):
        """Calculates graph node count, edge count, diameter, density.

        Args:
            network (:class:`Network`):
                The :class:`Network` object.
        """

        self._number_of_nodes = network.graph.vcount()
        self._number_of_edges = network.graph.ecount()
        self._diameter = network.graph.diameter(weights=self.edge_weight)
        self._density = network.graph.density()

    @_Compute._computed_property
    def number_of_nodes(self):
        """int: The total number of nodes."""
        return self._number_of_nodes

    @_Compute._computed_property
    def number_of_edges(self):
        """int: The total number of edges."""
        return self._number_of_edges

    @_Compute._computed_property
    def diameter(self):
        """int: The maximum number of edges that have to be traversed to get
        from one node to any other node. Also referred to as the maximum
        eccentricity, or the longest-shortest path of the graph.
        """
        return self._diameter

    @_Compute._computed_property
    def density(self):
        r"""float: The fraction of edges that exist compared to all possible
        edges in a complete graph:

        .. math::

           \rho = \frac{2e}{n(n-1)}

        """
        return self._density


class Clustering(_Compute):
    """Calculates cluster properties. Weights are not supported."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compute(self, network):
        """Computes local and average clustering coefficients.

        Args:
            network (:class:`Network`):
                The :class:`Network` object.
        """

        self._cc = network.graph.transitivity_local_undirected(mode="zero")
        self._acc = np.mean(self._cc)

    @_Compute._computed_property
    def clustering(self):
        r""":class:`np.ndarray`: Array of clustering coefficients,
        :math:`\delta_{i}` s. The clustering coefficient is the fraction of
        neighbors of a node that are directly connected to each other as well
        (forming a triangle):

        .. math::

           \delta_i = \frac{2*T_i}{k_i(k_i-1)}

        Where :math:`T_i` is the number of connected triples (visually
        triangles) on node :math:`i`.

        """
        return self._cc

    @_Compute._computed_property
    def average_clustering_coefficient(self):
        r"""float: The average clustering coefficient over nodes:

        .. math::

           \Delta = \frac{\sum_i{\delta}}{n}

        """
        return self._acc


class Assortativity(_Compute):
    """Assortativity refers to how related a node is to its neighbor's. In this
    module, similarity refers to similarity by degree.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compute(self, network):
        """Calculates assortativity by degree.

        Args:
            network (:class:`Network`):
                The :class:`Network` object.
        """

        self._assortativity = network.graph.assortativity_degree()

    @_Compute._computed_property
    def assortativity(self):
        r"""float: The assortativity coefficient, r, measures similarity of
        connections by node degree. This value approaches 1 if nodes with the
        same degree are directly connected to each other and approaches −1
        if nodes are all connected to nodes with different degree. A value
        near 0 indicates uncorrelated connections: :cite:`Newman2018`

        .. math::

           r = \frac{1}{\sigma_q^2}\sum_{jk} jk(e_{jk}-q_j * q_k)

        where :math:`q` is the *remaining degree distribution*,
        :math:`\sigma_{q}^2` is it variance. :math:`e_{jk}` is the joint
        probability distribution of the remaining degrees of the two vertices
        at either end of a randomly chosen edge.

        """
        return self._assortativity


class Closeness(_Compute):
    """Calculates closeness parameters. This module supports edge weights."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compute(self, network):
        """Computes node closeness and average closeness.

        Args:
            network (:class:`Network`):
                The :class:`Network` object.
        """

        self._closeness = network.graph.closeness(weights=self.edge_weight)
        self._ac = np.mean(self._closeness)

    @_Compute._computed_property
    def closeness(self):
        r""":class:`np.ndarray`: The closeness centrality of node :math:`i` is
        the reciprocal of the average shortest distance from node :math:`i` to
        all other nodes:

        .. math::

           C_{C}(i) = \frac{n-1}{\sum_{j=1}^{n-1}L(i,j)}

        where :math:`L(i,j)` is the shortest path between nodes :math:`i` and
        :math:`j`.

        """
        return self._closeness

    @_Compute._computed_property
    def average_closeness(self):
        r"""float: The average closeness:

        .. math::

           \Delta = \frac{\sum_i{C}}{n}

        """
        return self._ac


class Degree(_Compute):
    """Calculates degree. This module support node weights, for the calculation
    of weighted node degree, sometimes called "strength"."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compute(self, network):
        """Computes node degree and average degree.

        Args:
            network (:class:`Network`):
                The :class:`Network` object.
        """

        self._degree = network.graph.strength(weights=self.node_weight)
        self._ad = np.mean(self._degree)

    @_Compute._computed_property
    def degree(self):
        r""":class:`np.ndarray`: The number of edges connected to each node."""
        return self._degree

    @_Compute._computed_property
    def average_degree(self):
        r""":class:`np.ndarray`: The average number of edges connected to each
        node."""
        return self._ad
