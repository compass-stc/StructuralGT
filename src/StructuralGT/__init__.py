"""
**StructuralGT**

A software package for performing Graph Theory on microscopic TEM images. This software is a \
modified version of StructuralGT by Drew A. Vecchio: https://github.com/drewvecchio/StructuralGT.

    Copyright (C) 2025, the Regents of the University of Michigan.

        This program is free software: you can redistribute it and/or modify \
it under the terms of the GNU General Public License as published by \
the Free Software Foundation, either version 3 of the License, or \
(at your option) any later version. This program is distributed in \
the hope that it will be useful, but WITHOUT ANY WARRANTY; without \
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  \
See the GNU General Public License for more details. You should have received a copy \
of the GNU General Public License along with this program.  If not, see <https://www.gnu.org/licenses/>.

        Development Lead: Dickson Owuor

        Contributors: Nicholas A. Kotov

        Contact email: owuordickson@gmail.com
"""

# MODULES
from .compute.graph_analyzer import GraphAnalyzer, COMPUTING_DEVICE
from .imaging.base_image import BaseImage
from .imaging.image_processor import ImageProcessor, ALLOWED_IMG_EXTENSIONS
from .networks.fiber_network import FiberNetworkBuilder
from .networks.graph_skeleton import GraphSkeleton
from .utils.progress_update import ProgressUpdate
from .utils.config_loader import load_gtc_configs, load_gte_configs, load_img_configs
from .utils.sgt_utils import write_csv_file, write_gsd_file, plot_to_opencv


# Project Details
__version__ = "3.3.2"
__title__ = f"StructuralGT (v{__version__})"
__author__ = "Dickson Owuor"
__credits__ = "The Regents of the University of Michigan"

