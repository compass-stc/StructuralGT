from StructuralGT.util import _Compute
import numpy as np

class Betweenness(_Compute):
    """A module for calculating different extension of the classical
    edge betweenness centrality measure. In particular, calculates
    betweennesses which include geometric features of the network via weights
    and boundary conditions.
    """
    def __init__(self):
        pass

    def bounded_betweenness(self, sources, targets, weights=None):
        from StructuralGT import _bounded_betweenness_cast

        num_edges = self.Gr.ecount()
        _copy = copy.deepcopy(self.Gr)

        if weights is None:
            weights = np.ones(num_edges, dtype=np.double)
        else:
            weights = np.array(_copy.es[weights], dtype=np.double)

        cast = _bounded_betweenness_cast.PyCast(_copy._raw_pointer())

        cast.bounded_betweenness_compute(
            np.array(sources, dtype=np.longlong),
            np.array(targets, dtype=np.longlong),
            num_edges,
            weights,
        )

        return cast.bounded_betweenness

    def random_betweenness(self, sources, targets, weights=None):
        from StructuralGT import _random_betweenness_cast

        num_edges = self.Gr.ecount()
        _copy = copy.deepcopy(self.Gr)

        if weights is None:
            weights = np.ones(num_edges, dtype=np.double)
        else:
            weights = np.array(_copy.es[weights], dtype=np.double)

        cast = _random_betweenness_cast.PyCast(_copy._raw_pointer())

        cast.random_betweenness_compute(
            np.array(sources, dtype=np.longlong),
            np.array(targets, dtype=np.longlong),
            num_edges,
            weights,
        )

        return cast.random_betweenness

    def nonlinear_random_betweenness(self, sources, targets, incoming,
                                     weights=None):
        from StructuralGT import _nonlinear_random_betweenness_cast
        _copy = copy.deepcopy(self.Gr)

        #Add ghost node and edges from targets to ghost
        _copy.add_vertex(1)
        for target in targets:
            _copy.add_edge(self.Gr.vcount()-1,target)
        num_edges = _copy.ecount()

        #When passing weight vector, must add additional weights for edges
        #between targets and ghost node (added in cpp file)
        if weights is None:
            weights = np.ones(num_edges, dtype=np.double)
        else:
            mean = np.mean(np.array(self.Gr.es[weights]))

            weights = np.append(np.array(self.Gr.es[weights], dtype=np.double),
                                np.full(len(targets), mean, dtype=np.double)).astype(np.double)
            assert len(weights) == _copy.ecount()
        cast = _nonlinear_random_betweenness_cast.PyCast(_copy._raw_pointer())

        cast.nonlinear_random_betweenness_compute(
            np.array(sources, dtype=np.longlong),
            np.array(targets, dtype=np.longlong),
            np.array(np.ones(len(sources)), dtype=np.longlong),
            num_edges,
            weights,
        )

        return cast.nonlinear_random_betweenness

    def compute(self, network, sources, targets, skips=None, incoming=None,
                weights=None):
        r"""Compute different edge betweenness centralities of the graph.

        Args:
            network (:class:`Network`):
                The :class:`Network` object.
            sources (list):
                The set of source nodes, $S$.
            targets (list):
                The set of target nodes, $T$.
            weights (str, optional):
                The name of the edge attribute to be used in weighting the
                random walks. If omitted, an unweighted network is used.

        """

        self._bounded_betweenness = bounded_betweenness(network, sources, targets, weights)
        self._random_betweenness = random_betweenness_cast(network, sources, targets, weights)
        self._nonlinear_random_betweenness = nonlinear_random_betweenness(network, sources, targets, weights)

    @_Compute._computed_property
    def bounded(self):
        r"""Edge betweenness centrality over a subset of nodes.
        Sometimes called betweenness subset.

        .. math::

           c_B(v) =\sum_{s\in S,t \in T} \frac{\sigma(s, t|e)}{\sigma(s, t)}

        where $S$ is the set of sources, $T$ is the set of targets,
        $\sigma(s, t)$ is the number of shortest $(s, t)$-paths,
        and $\sigma(s, t|e)$ is the number of those paths
        passing through edge $e$ :cite:`Brandes2008` (which is unity for real 
        value weighted graphs). 
        """
        return self._bounded_betweenness

    @_Compute._computed_property
    def random_walk(self):
        r"""Compute random walk betweenness of edges. Adapted from
        :cite:`Newman2005` to calculate net random walker flow through `edges`
        instead of `nodes`. Also adapted to include several source and target
        nodes at once. To converse flow, number of source and target nodes
        must be equal. Full details given in :cite:`Martinez2024`.
        """
        return self._random_betweenness

    @_Compute._computed_property
    def nonlinear(self):
        """Similar to :meth:`random_walk` except flow is conserved by
        adding a ghost node and attaching it to all the target nodes. Flow
        constraints are enforced only at the source and ghost node. Full
        details are given in :cite:`Martinez2024`.
        """
        return self._nonlinear_random_betweenness
