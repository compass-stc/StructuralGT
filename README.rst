============
StructuralGT
============

Overview
========
A python package for the extraction and analysis of graphs from 2D and 3D experimental micrographs. Image processing techniques taken from `StructuralGT <https://github.com/drewvecchio/StructuralGT>`__.

Installation guide
==================


**StructuralGT** can  be built from source, via the
`public repository <https://github.com/compass-stc/StructuralGT>`__.
Prior to install, you will need to install some dependencies into your conda
environment. Note that installation will most likely be
successful if carried out in a new conda environment. While it is posisble to
obtain some of these dependencies with pip, installation will most likely be
sucessful when all dependencies are obtained with conda.

.. code:: bash

   git clone https://github.com/compass-stc/StructuralGT.git
   cd StructuralGT
   python3 -m pip install . --no-deps
   StructuralGT
