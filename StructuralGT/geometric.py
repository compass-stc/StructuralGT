from StructuralGT.util import _Compute
import numpy as np
import freud

class Nematic(_Compute):
    """Computes the nematic tensor of the graph. For details on how it 
    quantifies orientational anisotropy, see :cite:`Mottram`2014."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compute(self, network):
        """Computes the nematic tensor of the graph."""
        
        orientations = np.zeros((network.graph.ecount(), network.dim))
        for i,edge in enumerate(network.graph.es):
            orientations[i] = edge['pts'][0] - edge['pts'][-1]
        
        if network._2d:
            orientations = np.hstack((orientations, np.zeros((len(orientations),1))))
            
        nematic = freud.order.Nematic()
        nematic.compute(orientations)
        self._nematic = nematic

    @_Compute._computed_property
    def nematic(self):
        r"""The :class:`freud.order.Nematic` compute module, populated with 
        the nematic attributes. See the `freud documentation 
        <https://freud.readthedocs.io/en/latest/order.html#freud.order.Nematic>`_ 
        for more information."""

        return self._nematic

