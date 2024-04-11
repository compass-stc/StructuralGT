from StructuralGT.networks import Network, ParticleNetwork, Graph
import StructuralGT

import pytest
import shutil
import os

import options

_path = StructuralGT.__path__[0]
Small_path = _path + '/pytest/data/Small/'
AgNWN_path = _path + '/pytest/data/AgNWN/'

class TestNetwork:
    @pytest.fixture
    def test_binarize(self):

        shutil.rmtree(AgNWN_path + 'Binarized', ignore_errors=True)
        shutil.rmtree(AgNWN_path + 'HighThresh', ignore_errors=True)

        testNetwork = Network(AgNWN_path)
        testNetwork.binarize(options=options.agnwn)

        HighThresh = Network(AgNWN_path, child_dir='HighThresh')
        HighThresh.binarize(options=options.agnwn_high_thresh)
        HighThresh.img_to_skel()
        HighThresh.set_graph(write=False)

        return testNetwork

    @pytest.fixture
    def test_crop(self, test_binarize):
        testNetwork = test_binarize
        testNetwork.img_to_skel(crop=[0,500,0,500])

        return testNetwork

    def test_rotations(self, test_binarize):
        testNetwork = test_binarize
        testNetwork.img_to_skel(crop=[149, 868, 408, 1127], rotate=45)

    @pytest.fixture
    def test_weighting(self, test_crop):
        testNetwork = test_crop
        testNetwork.set_graph(weight_type=['FixedWidthConductance'], R_j=10,
                              rho_dim=2, write=False)

        return testNetwork

    def test_from_gsd(self):
        writeNetwork = Network(Small_path)
        writeNetwork.binarize(options=options.agnwn)
        writeNetwork.img_to_skel()
        writeNetwork.set_graph()

        testNetwork = Network.from_gsd(Small_path + 'Binarized/network.gsd')

        testNetwork.Gr.vs['o'][0]

class TestGraph:
    def test_from_gsd(self):
        testGraph = Graph(Small_path + 'Binarized/network.gsd')

        testGraph.vs['o'][0]
