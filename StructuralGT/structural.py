from StructuralGT.util import _Compute
import numpy as np

class Structural(_Compute):
    """Classical GT parameters. Calculates most of the parameters offered
    by the StructuralGT GUI :cite:`Vecchio2021`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compute(self, network):
        """Calculates graph diameter, density, assortativity by degree,
        and average clustering coefficient. Also calculates per node degree,
        closeness, betweenness, and clustering.

        Args:
            network (:class:`Network`):
                The :class:`Network` object.
        """

        self.vcount = network.graph.vcount()

        operations = [
                network.graph.diameter,
                network.graph.density,
                network.graph.transitivity_local_undirected,
                network.graph.assortativity_degree,
                network.graph.betweenness,
                network.graph.closeness,
                network.graph.degree,
        ]

        names = [
                "Diameter",
                "Density",
                "Clustering",
                "Degree_Assortativity",
                "Betweenness",
                "Closeness",
                "Degree"
        ]

        for operation, name in zip(operations, names):
            if name in ["Diameter", "Betweenness", "Closeness"]:
                setattr(self, name, operation(weights=self.weight_type))
            elif name == "Clustering":
                setattr(self, name, operation(mode="zero"))
            else:
                setattr(self, name, operation())

    @_Compute._computed_property
    def diameter(self):
        """int: The maximum number of edges that have to be traversed to get from 
        one node to any other node. Also referred to as the maximum
        eccentricity, or the longest-shortest path of the graph.
        """
        return self.Diameter

    @_Compute._computed_property
    def density(self):
        r"""float: The fraction of edges that exist compared to all possible
        edges in a complete graph:

        .. math::

           \rho = \frac{2e}{n(n-1)}

        """
        return self.Density

    @_Compute._computed_property
    def clustering(self):
        r""":class:`np.ndarray`: Array of clustering coefficients,
        :math:`\delta_{i}` s. The clustering coefficient is the fraction of
        neighbors of a node that are directly connected to each other as well
        (forming a triangle):

        .. math::

           \delta_i = \frac{2*T_i}{k_i(k_i-1)}

        Where :math:`T_i` is the number of connected triples (visually triangles)
        on node :math:`i`.

        """
        return self.Clustering

    @_Compute._computed_property
    def average_clustering_coefficient(self):
        r"""float: The average clustering coefficient over nodes:

        .. math::

           \Delta = \frac{\sum_i{\delta}}{n}

        """
        return np.mean(self.clustering)

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
        return self.Degree_Assortativity

    @_Compute._computed_property
    def betweenness(self):
        r""":class:`np.ndarray`: The betweenness centrality of node :math:`i` is a measure of how
        frequently the shortest path between other nodes :math:`u` and :math:`v` pass 
        through node :math:`i`:

        .. math::

           C_{B}(i) = \sum_{u,v}\frac{\sigma(u,v)}{\sigma(u,v \parallel i)}
        
        where :math:`\sigma(u,v)` represents the number of shortest 
        paths that exist between nodes :math:`u` and :math:`v`, with the term
        :math:`\sigma(u,v \parallel i)` representing the number of those paths that
        pass through node :math:`i`. For variations on this parameter, see the
        :class:`Betweenness` module.
        """
        return np.asarray(self.Betweenness)/(self.vcount-1)/(self.vcount-2)*2

    @_Compute._computed_property
    def closeness(self):
        r""":class:`np.ndarray`: The closeness centrality of node :math:`i` is the
        reciprocal of the average shortest distance from node :math:`i` to all 
        other nodes:

        .. math::

           C_{C}(i) = \frac{n-1}{\sum_{j=1}^{n-1}L(i,j)}

        where :math:`L(i,j)` is the shortest path between nodes :math:`i` and :math:`j`. 

        """
        return self.Closeness

    @_Compute._computed_property
    def degree(self):
        r""":class:`np.ndarray`: The number of edges connected to each node.
        """
        return self.Degree
