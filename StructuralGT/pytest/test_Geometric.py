# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import StructuralGT
from StructuralGT.geometric import Nematic

_path = StructuralGT.__path__[0]


class TestNematic:
    def test_random(self, random_stick):
        # Obtain a random graph
        testNetwork = random_stick

        # Instantiate a compute module and run calculation
        ComputeModule = Nematic()
        ComputeModule.compute(testNetwork)

    def test_aligned(self, aligned_stick):
        # Obtain a random graph
        testNetwork = aligned_stick

        # Instantiate a compute module and run calculation
        ComputeModule = Nematic()
        ComputeModule.compute(testNetwork)
