from StructuralGT.electronic import Electronic

import igraph as ig
import pytest
import numpy.testing as npt

import StructuralGT
_path = StructuralGT.__path__[0]

class TestElectronic:
    @pytest.fixture
    def test_compute(self, conductive):
        #Obtain a conductive graph
        testNetwork = conductive

        #Instantiate a compute module and run calculation
        ComputeModule = Electronic()
        ComputeModule.compute(testNetwork, 10, 0, [[0,50],[testNetwork.shape[0]-50, testNetwork.shape[0]]])

        return ComputeModule

    def test_Kirchhoff(self, test_compute):
        #Ensure Kirchhoff's Law satisfied
        ComputeModule = test_compute

        npt.assert_allclose((ComputeModule.P[-2] - ComputeModule.P[-1])/ComputeModule.effective_resistance,
                            1,
                            atol=1e-2
                            )
