"""
**StructuralGT**

    A software package for performing Graph Theory on digital network images. This software is a modified version of
StructuralGT by Drew A. Vecchio: https://github.com/drewvecchio/StructuralGT.

    Copyright (C) 2025, the Regents of the University of Michigan.

    This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later
version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU GPU v3 for more details. You
should have received a copy of the GNU General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

    Contributors: Dickson Owuor, Drew Vecchio, Alain Kadar, Nicholas A. Kotov

    Contact email: owuordickson@gmail.com
"""

import json
import os

# MODULES
from .metrics.graph_analyzer import GraphAnalyzer
from .networks.graph_skeleton import GraphSkeleton
from .networks.fiber_network import FiberNetworkBuilder
from .imaging.network_processor import NetworkProcessor

current_dir = os.path.dirname(__file__)
file_path = os.path.join(current_dir, 'metadata.json')
with open(file_path, 'r') as json_file:
    metadata = json.load(json_file)


# Project Details
__version__ = "3.5.1"
__title__ = f"StructuralGT (v{__version__})"
__author__ = "Dickson Owuor, Alain Kadar, Drew Vecchio, Nicholas A. Kotov"
__credits__ = "The Regents of the University of Michigan"
__C_FLAG__ = metadata["C_FLAG"]



# Packages available in 'from StructuralGT import *'
__all__ = ['__version__', 'GraphAnalyzer', 'GraphSkeleton', 'FiberNetworkBuilder', 'NetworkProcessor']
