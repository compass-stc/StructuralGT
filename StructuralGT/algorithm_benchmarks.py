import base
import timeit
import network
import numpy as np

"""Benchmarks for vaious SGT algorithms and functions"""


def effective_resistance():
    """Benchmark for comparing 2 different approaches for finding the effective
    resistance between 2 vertices in a resistive network

    1. Klein, D. J. & Randić, M. Resistance distance. J. Math. Chem. 1993 121 12, 81–95 (1993)
    From the pseudoinverse of the weighted Laplacian matrix

    2. 
    From the determinants of submatrices of the weighted Laplacian matrix
    """

    setup = """
    crop=400
    g = network.ResistiveNetwork('TestData/AgNWN_10um')
    g.binarize()
    g.stack_to_gsd(crop=[0,crop,0,crop])
    g.G_u()
    g.potential_distribution(0, [0,crop], [crop-20,crop])
    G = g.Gr_connected
    """

    def Klein(G, source, sink):
        L = np.asarray(G.laplacian(weights='weight'))
        Linv = np.linalg.pinv(L)

        rij = Linv[source,source] + Linv[sink,sink] - 2*Linv[source,sink]
        print(rij)

    def Bapat(G, source, sink):
        L=np.asarray(G.laplacian(weights='weight'))
        Li = np.delete(np.delete(L, source, axis=0), source, axis=1)
        Lij = np.delete(np.delete(Li, sink, axis=0), sink, axis=1)

        (signi, logdeti) = np.linalg.slogdet(Li)
        deti = signi * np.exp(logdeti)
        (signij, logdetij) = np.linalg.slogdet(Lij)
        detij = signij * np.exp(logdetij)

        #deti = np.linalg.det(Li)
        #detij = np.linalg.det(Lij)

        rij = detij/deti
        print(rij)

    tests = {
        "Klein": """Klein(G,1,100)""",
        "Bapat": """Bapat(G,1,100)""",
    }

    results = {}
    for test_name, test_stmt in tests.items():
        times = timeit.repeat(
            setup=setup, stmt=test_stmt, repeat=1, number=1, globals=globals()
        )
        #avg_time = sum(times) / len(times)
        results[test_name] = times

    for test_name, result in sorted(results.items(), key=lambda x: x[1]):
        print(test_name, result)
