"""
StructuralGT

A python package for automated graph theory analysis
of digital structural network images.
"""

import json
from pathlib import Path
from .binarizer import Binarizer

current_dir = Path(__file__).parent
file_path = current_dir / "metadata.json"
with open(file_path) as json_file:
    metadata = json.load(json_file)

__version__ = "1.0.1b1"
__author__ = "Alain Kadar"
__credits__ = "The Regents of the University of Michigan"
__C_FLAG__ = metadata["C_FLAG"]
