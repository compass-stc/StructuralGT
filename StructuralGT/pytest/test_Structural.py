from StructuralGT.structural import Structural
from network_factory import fibrous
import igraph as ig
import pytest
from networkx import diameter, density, clustering, average_clustering, degree_assortativity_coefficient, betweenness_centrality, closeness_centrality
import numpy.testing as npt


class TestUnweightedStructural:
    @pytest.fixture
    def test_compute(self):
        #Obtain an unweighted connected graph
        testNetwork = fibrous()
        testGraph = testNetwork.graph.to_networkx()

        #Instantiate a compute module and run calculation
        ComputeModule = Structural()
        ComputeModule.compute(testNetwork)

        return ComputeModule, testGraph

    def test_diameter(self, test_compute):
        ComputeModule, testGraph = test_compute
        npt.assert_allclose(
                ComputeModule.diameter,
                diameter(testGraph),
                atol=1e-2,
                )

    def test_density(self, test_compute):
        ComputeModule, testGraph = test_compute
        npt.assert_allclose(
                ComputeModule.density,
                density(testGraph),
                atol=1e-2,
                )

    def test_average_clustering(self, test_compute):
        ComputeModule, testGraph = test_compute
        npt.assert_allclose(
                ComputeModule.average_clustering_coefficient,
                average_clustering(testGraph),
                atol=1e-2,
                )

    def test_assortativity(self, test_compute): 
        ComputeModule, testGraph = test_compute
        npt.assert_allclose(
                ComputeModule.assortativity,
                degree_assortativity_coefficient(testGraph),
                atol=1e-2,
                )
    
    def test_betweenness(self, test_compute): 
        ComputeModule, testGraph = test_compute
        npt.assert_allclose(
                ComputeModule.betweenness,
                betweenness_centrality(testGraph),
                atol=1e-2,
                )

    def test_closenness(self, test_compute): 
        ComputeModule, testGraph = test_compute
        npt.assert_allclose(
                ComputeModule.closeness,
                closeness_centrality(testGraph),
                atol=1e-2,
                )

class TestWeightedStructural:
    @pytest.fixture
    def test_compute(self):
        #Obtain an unweighted connected graph
        testNetwork = fibrous(weight_type=['Length'])
        testGraph = testNetwork.graph.to_networkx()

        #Instantiate a compute module and run calculation
        ComputeModule = Structural(weight_type='Length')
        ComputeModule.compute(testNetwork)

        return ComputeModule, testGraph

    def test_diameter(self, test_compute):
        ComputeModule, testGraph = test_compute
        npt.assert_allclose(
                ComputeModule.diameter,
                diameter(testGraph, weight='Length'),
                atol=1e-2,
                )
