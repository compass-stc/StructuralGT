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
        
        _orientations = np.zeros((network.graph.ecount(), network.dim))
        for i,edge in enumerate(network.graph.es):
            _orientations[i] = edge['pts'][0] - edge['pts'][-1]
        
        if network._2d:
            _orientations = np.hstack((_orientations, np.zeros((len(_orientations),1))))
            
        nematic = freud.order.Nematic()
        nematic.compute(_orientations)
        self._nematic = nematic
        self._orientations = _orientations

    @_Compute._computed_property
    def nematic(self):
        r"""The :class:`freud.order.Nematic` compute module, populated with 
        the nematic attributes. See the `freud documentation 
        <https://freud.readthedocs.io/en/latest/order.html#freud.order.Nematic>`_ 
        for more information."""

        return self._nematic
    
    @_Compute._computed_property
    def orientations(self):
        r"""The edge orientations.""" 

        return self._orientations
