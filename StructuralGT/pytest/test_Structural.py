from StructuralGT.structural import (
        Size, 
        Clustering,
        Assortativity,
        Closeness,
        Degree
    )
import igraph as ig
import pytest
from networkx import (
        average_clustering, 
        betweenness_centrality,
        closeness_centrality,
        clustering, 
        degree_assortativity_coefficient,
        density, 
        diameter, 
        Graph
    )
import numpy.testing as npt
import numpy as np

class TestSize:
    @pytest.fixture
    def test_compute(self, conductive):
        testNetwork = conductive
        testGraph = testNetwork.graph.to_networkx(create_using=Graph)

        #Instantiate a compute module and run calculation
        ComputeModule = Size()
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

class TestClustering:
    @pytest.fixture
    def test_compute(self, conductive):
        #Obtain an unweighted connected graph
        testNetwork = conductive
        testGraph = testNetwork.graph.to_networkx(create_using=Graph)

        #Instantiate a compute module and run calculation
        ComputeModule = Clustering()
        ComputeModule.compute(testNetwork)

        return ComputeModule, testGraph

    def test_average_clustering(self, test_compute):
        ComputeModule, testGraph = test_compute
        npt.assert_allclose(
                ComputeModule.average_clustering_coefficient,
                average_clustering(testGraph),
                atol=1e-2,
                )


class TestAssortativity:
    @pytest.fixture
    def test_compute(self, conductive):
        #Obtain an unweighted connected graph
        testNetwork = conductive
        testGraph = testNetwork.graph.to_networkx(create_using=Graph)

        #Instantiate a compute module and run calculation
        ComputeModule = Assortativity()
        ComputeModule.compute(testNetwork)

        return ComputeModule, testGraph

    def test_assortativity(self, test_compute): 
        ComputeModule, testGraph = test_compute
        npt.assert_allclose(
                ComputeModule.assortativity,
                degree_assortativity_coefficient(testGraph),
                atol=1e-2,
                )
    
class TestCloseness:
    @pytest.fixture
    def test_compute(self, conductive):
        #Obtain an unweighted connected graph
        testNetwork = conductive
        testGraph = testNetwork.graph.to_networkx(create_using=Graph)

        #Instantiate a compute module and run calculation
        ComputeModule = Closeness()
        ComputeModule.compute(testNetwork)

        return ComputeModule, testGraph

    def test_closenness(self, test_compute): 
        ComputeModule, testGraph = test_compute
        npt.assert_allclose(
                ComputeModule.closeness,
                np.fromiter(closeness_centrality(testGraph).values(),
                            dtype=float),
                rtol=1e-2,
                )

class TestDegree:
    @pytest.fixture
    def test_compute(self, conductive):
        #Obtain an unweighted connected graph
        testNetwork = conductive
        testGraph = testNetwork.graph.to_networkx(create_using=Graph)

        #Instantiate a compute module and run calculation
        ComputeModule = Degree()
        ComputeModule.compute(testNetwork)

        return ComputeModule, testGraph

    #TODO: Add tests

