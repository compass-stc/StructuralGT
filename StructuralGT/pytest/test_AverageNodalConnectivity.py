# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import numpy as np
import numpy.testing as npt

from StructuralGT.average_nodal_connectivity import AverageNodalConnectivity


class TestAverageNodalConnectivity:
    def test(self, fibrous):
        # Obtain a connected graph
        testNetwork = fibrous

        # Instantiate a compute module and run calculation
        ComputeModule = AverageNodalConnectivity()
        ComputeModule.compute(testNetwork)

        # Compute ANC manually
        vals = []
        for i in range(testNetwork.graph.vcount()):
            for j in range(i + 1, testNetwork.graph.vcount()):
                val = testNetwork.graph.vertex_connectivity(
                    source=j, target=i, neighbors="negative"
                )
                if val == -1:
                    continue
                vals.append(val)

        npt.assert_allclose(
            ComputeModule.average_nodal_connectivity,
            np.mean(np.asarray(vals)),
            rtol=1e-2,
        )
