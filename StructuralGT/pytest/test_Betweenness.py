# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import numpy.testing as npt
import pytest

import StructuralGT


class TestNodeBoundaryBetweenness:
    @pytest.mark.skipif(
        not StructuralGT.__C_FLAG__, reason="Betweenness module not compiled"
    )
    def test(self, fibrous):
        from StructuralGT.betweenness import NodeBoundaryBetweenness

        # Obtain a connected graph
        testNetwork = fibrous

        TEST_NODE = 10
        SOURCES = range(0, 8)
        TARGETS = range(
            testNetwork.graph.vcount() - 8, testNetwork.graph.vcount()
        )

        # Instantiate a compute module and run calculation
        ComputeModule = NodeBoundaryBetweenness()
        ComputeModule.compute(testNetwork, SOURCES, TARGETS)

        # Compute betweenness manually
        total = 0
        for i in SOURCES:
            sps = testNetwork.graph.get_all_shortest_paths(i)
            for j in TARGETS:
                count = 0
                mask = (x[-1] == j for x in sps)
                sp = [b for a, b in zip(mask, sps) if a]
                for spi in sp:
                    if TEST_NODE in spi:
                        count += 1
                total += count / len(sp)
        total /= 2

        npt.assert_allclose(
            total, ComputeModule.vertex_boundary_betweenness[TEST_NODE]
        )
