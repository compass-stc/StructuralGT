from StructuralGTEdits import physical_networks, base
import StructuralGTEdits
import pytest

_path = StructuralGTEdits.__path__[0]

def test_3D():
    N = physical_networks.StructuralNetwork(_path + '/pytest/data/Rectangle1')
    N.binarize()
    N.stack_to_gsd()
    N.set_graph()
    N.node_calc()
    N.Node_labelling(N.Degree[0],'Degree','test.gsd')

def test_3D_crop():
    N = physical_networks.StructuralNetwork(_path + '/pytest/data/Rectangle1')
    N.binarize()
    N.stack_to_gsd(crop=[0,550,0,550,0,2])
    N.set_graph()
    N.node_calc()
    N.Node_labelling(N.Degree[0],'Degree','test.gsd')

def test_2D():
    N = physical_networks.StructuralNetwork(_path + '/pytest/data/AgNWN')
    N.binarize()
    N.stack_to_gsd()
    N.set_graph()
    N.node_calc()
    N.Node_labelling(N.Degree[0],'Degree','test.gsd')

def test_2D_crop():
    N = physical_networks.StructuralNetwork(_path + '/pytest/data/AgNWN')
    N.binarize()
    N.stack_to_gsd(crop=[0,550,0,550])
    N.set_graph()
    N.node_calc()
    N.Node_labelling(N.Degree[0],'Degree','test.gsd')

