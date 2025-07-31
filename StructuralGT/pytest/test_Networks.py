# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import shutil
import os

import numpy as np
import pandas as pd
from StructuralGT import error
from StructuralGT.networks import Graph, Network, PointNetwork

import options
import pytest

Small_path = "StructuralGT/pytest/data/Small/"
AgNWN_path = "StructuralGT/pytest/data/AgNWN/"
ANF_path = "StructuralGT/pytest/data/ANF/"
PointNetwork_path = "StructuralGT/pytest/data/Seeds/"
img_path = "StructuralGT/pytest/data/loose_img.tiff"


class TestNetwork:
    def test_3d_constructor(self):
        with pytest.raises(error.ImageDirectoryError):
            testNetwork = Network(ANF_path, dim=3, prefix="wrong_prefix")

        testNetwork = Network(ANF_path, dim=3, prefix="slice", depth=[3, 287])

        testNetwork = Network(ANF_path, dim=3, depth=[281, 288])

        testNetwork = Network(ANF_path, dim=3, prefix="slice")
        assert len(testNetwork.image_stack) == 12

        # return testNetwork
        # uncomment if 3D network becomes required as a fixture in other tests

    @pytest.fixture
    def test_2d_constructor(self):
        with pytest.raises(error.ImageDirectoryError):
            testNetwork = Network(AgNWN_path, prefix="wrong_prefix")

        with pytest.warns(UserWarning):
            testNetwork = Network(AgNWN_path)

        return Network(AgNWN_path, prefix="slice")

    @pytest.fixture
    def test_binarize(self, test_2d_constructor):
        test_2d_constructor.binarize(options=options.agnwn)

        return test_2d_constructor

    def test_graph(self, test_2d_constructor):
        shutil.rmtree(AgNWN_path + "Binarized", ignore_errors=True)
        shutil.rmtree(AgNWN_path + "HighThresh", ignore_errors=True)

        testNetwork = Network(AgNWN_path)
        testNetwork.binarize(options=options.agnwn)

        HighThresh = Network(AgNWN_path, binarized_dir="HighThresh")
        HighThresh.binarize(options=options.agnwn_high_thresh)

        with pytest.raises(AttributeError):
            HighThresh.set_graph()

        HighThresh.img_to_skel()
        HighThresh.set_graph(write=False)

    @pytest.fixture
    def test_crop(self, test_binarize):
        testNetwork = test_binarize
        testNetwork.img_to_skel(crop=[0, 500, 0, 500])

        return testNetwork

    def test_rotations(self, test_binarize):
        testNetwork = test_binarize
        testNetwork.img_to_skel(crop=[149, 868, 408, 1127], rotate=45)

    def test_weighting(self, test_crop):
        testNetwork = test_crop
        testNetwork.set_graph(
            weight_type=["FixedWidthConductance"],
            R_j=10,
            rho_dim=2,
            write=False,
        )

    def test_from_gsd(self):
        writeNetwork = Network(Small_path, binarized_dir="HighThresh")
        writeNetwork.binarize(options=options.agnwn)
        writeNetwork.img_to_skel()
        writeNetwork.set_graph()

        testNetwork = Network.from_gsd(Small_path + "HighThresh/network.gsd")

        testNetwork.Gr.vs["o"][0]

    def test_from_img_file_path(self):
        with pytest.warns(UserWarning):
            testNetwork = Network(img_path)

        testNetwork.binarize(options=options.agnwn)
        testNetwork.img_to_skel()
        testNetwork.set_graph()

        dir_name = os.path.splitext(img_path)[0]
        os.rename(dir_name + "/loose_img.tiff", img_path)
        shutil.rmtree(dir_name)
        print("run")


class TestGraph:
    def test_from_gsd(self):
        testGraph = Graph(Small_path + "Binarized/network.gsd")
        testGraph.vs["o"][0]

ATTR_VALUES = {
            "periodic": False,
            "cutoff": 1200,
            "dim": 3,
        }
class TestPointNetwork:
    def test_write(self):
        positions = pd.read_csv(PointNetwork_path + 'seed_stats.csv')
        positions = positions[
            [
                "Center Of Mass X (µm)",
                "Center Of Mass Y (µm)",
                "Center Of Mass Z (µm)",
            ]
        ]
        positions = positions.values

        N = PointNetwork(positions, ATTR_VALUES["cutoff"])
        N.point_to_skel()

        assert hasattr(N, "graph")

        ATTR_VALUES['box'] = N.box

        N.node_labelling([np.ones(N.graph.vcount())], ["Ones"],
                         filename=PointNetwork_path + 'labelled.gsd')

    def test_from_gsd(self):
        N = PointNetwork.from_gsd(PointNetwork_path + "labelled.gsd")

        assert ATTR_VALUES['periodic'] == N.periodic
        assert ATTR_VALUES['cutoff'] == N.cutoff
        assert np.all(ATTR_VALUES['box'] == N.box)
