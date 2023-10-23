from StructuralGT import physical_networks, base
import StructuralGT
import pytest
import os
import shutil

_path = StructuralGT.__path__[0]

@pytest.fixture(params=[pytest.param(_path+'/pytest/data/AgNWN'),
                        pytest.param(_path+'/pytest/data/ANF')])
def binarize(request):
    _dir = request.param
    if os.path.isdir(_dir+'/Binarized'): shutil.rmtree(_dir+'/Binarized')

    N = StructuralGT.physical_networks.ResistiveNetwork(_dir)
    N.binarize()

    #assert N.img_bin.shape == N.img.shape

    return N

@pytest.fixture
def gsd(binarize):
    N = binarize
    if N._2d:
        N.stack_to_gsd(crop=[149, 868, 408, 1127], rotate=45) 
    else:
        N.stack_to_gsd(crop=[0,100,0,90,4,9])

    return N

@pytest.fixture
def graph(gsd):
    N = gsd
    N.set_graph(weight_type=['FixedWidthConductance'], sub=True)

    return N

@pytest.fixture
def potential(graph):
    N = graph
    if N._2d:
        N.potential_distribution(0,[0,20],[180,200],R_j=10)
    else:
        N.potential_distribution(0,[0,20],[70,90],R_j=10)

    return N

def test_node_labelling(potential):
    N = potential
    N.Node_labelling(N.P,'P','test.gsd') 
