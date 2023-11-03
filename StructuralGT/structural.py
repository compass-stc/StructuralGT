from StructuralGT.util import _Compute

class Structural(_Compute):
    """Classical GT parameters. Calculates most of the parameters offered
    by the StructuralGT GUI :cite:`Vecchio2021`.
    """
    def __init__(self):
        pass

    def compute(self, network, skips=None):
        operations = [
                network.graph.diameter,
                network.graph.density,
                network.graph.transitivity_undirected,
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
            setattr(self, name, operation())

    @_Compute._computed_property
    def diameter(self):
        """The maximum number of edges that have to be traversed to get from 
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

        r"""float: fraction of neighbors of a node that are directly connected to each other as well (forming a triangle). Ti is the number of connected triples (visually triangles) on node i.
        

        """
        return self.Clustering

    @_Compute._computed_property
    def diameter(self):
        return self.Diameter
    @_Compute._computed_property
    def diameter(self):
        return self.Diameter
    @_Compute._computed_property
    def diameter(self):
        return self.Diameter
    @_Compute._computed_property
    def diameter(self):
        return self.Diameter

    @_Compute._computed_property
    def diameter(self):
        return self.Diameter
    @_Compute._computed_property
    def diameter(self):
        return self.Diameter
    @_Compute._computed_property
    def diameter(self):
        return self.Diameter
    @_Compute._computed_property
    def diameter(self):
        return self.Diameter
    @_Compute._computed_property
    def diameter(self):
        return self.Diameter
