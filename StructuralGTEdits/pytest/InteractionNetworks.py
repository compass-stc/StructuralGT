from StructuralGTEdits import interaction_networks, base
import StructuralGTEdits
import pytest

_path = StructuralGTEdits.__path__[0]

def test_find_node():
    N = interaction_networks.InteractionNetwork(_path + '/pytest/data/ANF')
    N.binarize()
    N.set_graph([0,1000,0,1000,0,4])
    N.to_gsd()
    N.node_calc()
    N.Node_labelling(N.Degree[0],'Degree','test.gsd')
