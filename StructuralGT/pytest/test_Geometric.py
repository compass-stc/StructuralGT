from StructuralGT.geometric import Nematic

import pytest
import numpy.testing as npt

import StructuralGT
_path = StructuralGT.__path__[0]

class TestNematic:
    def test_random(self, random_stick):
        #Obtain a random graph
        testNetwork = random_stick

        #Instantiate a compute module and run calculation
        ComputeModule = Nematic()
        ComputeModule.compute(testNetwork)

    def test_aligned(self, aligned_stick):
        #Obtain a random graph
        testNetwork = aligned_stick

        #Instantiate a compute module and run calculation
        ComputeModule = Nematic()
        ComputeModule.compute(testNetwork)

