from StructuralGT.geometric import Nematic
from network_factory import random_stick

import pytest
import numpy.testing as npt

import StructuralGT
_path = StructuralGT.__path__[0]

class TestNematic:
    def test_random(self):
        #Obtain a random graph
        testNetwork = random_stick(aligned=False)

        #Instantiate a compute module and run calculation
        ComputeModule = Nematic()
        ComputeModule.compute(testNetwork)

    def test_aligned(self):
        #Obtain a random graph
        testNetwork = random_stick()

        #Instantiate a compute module and run calculation
        ComputeModule = Nematic()
        ComputeModule.compute(testNetwork)

