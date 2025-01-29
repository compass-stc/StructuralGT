# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import copy

from StructuralGT import _average_nodal_connectivity_cast
from StructuralGT.util import _Compute


class AverageNodalConnectivity(_Compute):
    """A module for calculating the average nodal connectivity.
    Written separately because it is computationally very expensive, yet has
    been shown to correlate well with material properties.REF
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compute(self, network):
        """Computes the average nodal connectivity."""
        _copy = copy.deepcopy(network.graph)

        cast = _average_nodal_connectivity_cast.PyCast(_copy._raw_pointer())

        cast.average_nodal_connectivity_compute()

        self._average_nodal_connectivity = cast.average_nodal_connectivity

    @_Compute._computed_property
    def average_nodal_connectivity(self):
        r"""The nodal connectivity :math:`\kappa(i,j)` , is the minimum number
        of edges that would need to be removed to disconnect nodes
        :math:`i` and :math:`j`. The average nodal connectivity is the
        connectivity value averaged over all pairs of nodes:

        .. math::

            \bar{\kappa} = 2\frac{\sum_{i \neq j}\kappa(i,j)}{n(n-1)}

        """
        return self._average_nodal_connectivity
