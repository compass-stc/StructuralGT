from StructuralGT.average_nodal_connectivity import AverageNodalConnectivity
from network_factory import fibrous

import igraph as ig
import pytest
from networkx import average_node_connectivity
import numpy.testing as npt


class TestAverageNodalConnectivity:
    def test(self):
        #Obtain a connected graph
        testNetwork = fibrous()
        testGraph = testNetwork.graph.to_networkx()

        #Instantiate a compute module and run calculation
        ComputeModule = AverageNodalConnectivity()
        ComputeModule.compute(testNetwork)

        #Check that the StructuralGT and networkx values are equal
        npt.assert_allclose(ComputeModule.average_nodal_connectivity,
                            average_node_connectivity(testGraph),
                            rtol=1e-2
                            )

