# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import os
import shutil
from pathlib import Path

import numpy as np
import options
import pandas as pd
import pytest

import StructuralGT
from StructuralGT import error
from StructuralGT.networks import Graph, Network, PointNetwork

Small_path = "StructuralGT/pytest/data/Small/"
AgNWN_path = "StructuralGT/pytest/data/AgNWN/"
ANF_path = "StructuralGT/pytest/data/ANF/"
PointNetwork_path = "StructuralGT/pytest/data/Seeds/"
EdgeList_path = "StructuralGT/pytest/data/Bonds/"
img_path = "StructuralGT/pytest/data/loose_img.tiff"

_path = Path(StructuralGT.__path__[0])
out_path = _path / "pytest/data/out_dir"

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
    def test_2d_binarize(self, test_2d_constructor):
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
    def test_crop(self, test_2d_binarize):
        testNetwork = test_2d_binarize
        testNetwork.img_to_skel(crop=[0, 500, 0, 500])

        return testNetwork

    def test_rotations(self, test_2d_binarize):
        testNetwork = test_2d_binarize
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


class TestGraph:
    def test_from_gsd(self):
        testGraph = Graph(Small_path + "Binarized/network.gsd")
        testGraph.vs["o"][0]

class TestDecoupledIO:
    """
    "DecoupledIO" refers to the ***. However because this is the IO employed
    by the GUI, this testing class is included to rigorously ensure that
    such IO decoupling is well-behaved.
    """

    @pytest.fixture
    def test_2d_constructor(self):

        return Network(AgNWN_path, binarized_dir=out_path)

    @pytest.fixture
    def test_2d_binarize(self, test_2d_constructor):
        test_2d_constructor.binarize(options=options.agnwn)

        return test_2d_constructor

    def test_2d_graph(self, test_2d_binarize):
        test_2d_binarize.img_to_skel()
        test_2d_binarize.set_graph()

        assert Path(out_path / "network.gsd").exists()
        os.remove(Path(out_path / "network.gsd"))

    @pytest.fixture
    def test_3d_constructor(self):

        testNetwork = Network(ANF_path,
                              dim=3, prefix="slice",
                              binarized_dir=out_path)
        assert len(testNetwork.image_stack) == 12

        return testNetwork

    @pytest.fixture
    def test_3d_binarize(self, test_3d_constructor):
        test_3d_constructor.binarize(options=options.anf)

        return test_3d_constructor

    def test_3d_graph(self, test_2d_binarize):
        test_2d_binarize.img_to_skel()
        test_2d_binarize.set_graph()

        assert Path(out_path / "network.gsd").exists()

ATTR_VALUES = {
    "periodic": False,
    "cutoff": 1200,
    "dim": 3,
}


class TestPointNetwork:
    def test_write_cutoff(self):
        positions = pd.read_csv(PointNetwork_path + "seed_stats.csv")
        positions = positions[
            [
                "Center Of Mass X (µm)",
                "Center Of Mass Y (µm)",
                "Center Of Mass Z (µm)",
            ]
        ]
        positions = positions.values

        N = PointNetwork(positions, {"r_max": ATTR_VALUES["cutoff"]})
        N.set_graph()

        assert hasattr(N, "graph")

        ATTR_VALUES["box"] = N.box

        N.node_labelling(
            [np.ones(N.graph.vcount())],
            ["Ones"],
            filename=PointNetwork_path + "labelled.gsd",
        )

    def test_write_edgelist(self):
        # Read edge list with whitespace as delimiter
        df = pd.read_csv(EdgeList_path + "Connectivity.dat", sep=r"\s+")
        edge_list = df[["node1", "node2"]].values
        edge_list -= 1  # Convert to 0-based indexing

        # Read node positions
        pos_df = pd.read_csv(EdgeList_path + "Node_positions.dat", sep=r"\s+")
        positions = pos_df[["x", "y", "z"]].values

        N = PointNetwork(positions, edge_list)
        N.set_graph()

        assert hasattr(N, "graph")

        N.node_labelling(
            [np.ones(N.graph.vcount())],
            ["Ones"],
            filename=EdgeList_path + "labelled.gsd",
        )

    def test_from_gsd(self):
        N = PointNetwork.from_gsd(
            PointNetwork_path + "labelled.gsd",
            {"r_max": ATTR_VALUES["cutoff"]},
        )

        assert ATTR_VALUES["periodic"] == N.periodic
        assert np.all(ATTR_VALUES["box"] == N.box)
