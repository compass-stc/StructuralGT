============
StructuralGT
============

Overview
========
A python package for the extraction and analysis of graphs from 2D and 3D experimental micrographs. Image processing techniques taken from `StructuralGT <https://github.com/drewvecchio/StructuralGT>`__.

Installation guide
==================
**StructuralGT** is available on conda-forge for the *linux-64*, *osx-64*, and *win-64*
architectures. Install with

.. code:: bash

   conda install conda-forge::structuralgt

**StructuralGT** can also be built from source, via the
[public repository](https://github.com/compass-stc/StructuralGT).
Prior to install, you will need to install some dependencies into your conda
environment. Note that installation will most likely be
successful if carried out in a new conda environment. While it is posisble to
obtain some of these dependencies with pip, installation will most likely be
sucessful when all dependencies are obtained with conda.

.. code:: bash

   git clone https://github.com/compass-stc/StructuralGT.git
   conda install eigen igraph cython tbb tbb-devel numpy cython scikit-build cmake
   cd StructuralGT
   python3 -m pip install .

You can verify successful installation by installing pytest and running the
included tests:

.. code:: bash

   conda install pytest
   pytest

Examples
========
For a tutorial on the software's use, consult our
[examples repository](https://github.com/compass-stc/StructuralGT-Examples).

Documentation
=============
To extend the above examples to novel analysis in your own work, you should
consult the documentation, which is avaiable at ... . You can also build the
documentation from source.
