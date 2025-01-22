from StructuralGT.util import _Compute
import numpy as np
import freud

def LargestRotatingCrop(image_shape):
    """Returns the crop coordinates for the largest square that would remain 
    inside during any rotation of the image. Supports 2D images only.

    Args:
        image_shape (tuple): The dimensions of the image to be cropped.

    Returns:
        (list): The coordinates of the crop in the format [L1,L2,L3,L4], where 
        L1 and L2 are the lower and upper x-coordinates of the crop, and L3 and 
        L4 are the lower and upper y-coordinates of the crop.
    """

    short_length = image_shape[image_shape == max(image_shape)]
    long_length = max(image_shape)
    rotated_diagonal_length = (short_length**2/2)**0.5
    
    L1 = int((short_length - rotated_diagonal_length)/2)
    L2 = int(rotated_diagonal_length+L1)
    L3 = int((long_length - rotated_diagonal_length)/2)
    L4 = int(rotated_diagonal_length+L3)
    
    return [L1,L2,L3,L4]

class Nematic(_Compute):
    """Computes the nematic tensor of the graph. For details on how it 
    quantifies orientational anisotropy, see :cite:`Mottram2014`. If the edge
    occupies a single voxel (and therefore has a zero vector orientation),
    it is not used in calculating the nematic tensor. However it is still
    returned as past of the orientations array so that the length of the
    orientations array is equal to the edge count."""

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
        nematic.compute(_orientations[np.where(_orientations.any(axis=1))[0]])
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
