from StructuralGTEdits import interaction_networks, base
import StructuralGTEdits
import pytest

_path = StructuralGTEdits.__path__[0]

def test_find_node():
    N = physical_networks.InteractionNetwork(_path + '/pytest/data/Rectangle1')
    N.binarize()
    N.stack_to_gsd()
    N.G_u()
    N.node_calc()
    N.Node_labelling(N.Degree[0],'Degree','test.gsd')
