============
StructuralGT
============

Overview
========
A python package for the extraction and analysis of graphs from 2D and 3D experimental micrographs. Image processing techniques taken from `StructuralGT <https://github.com/drewvecchio/StructuralGT>`__.
*StructuralGT* is available as an API based package, or GUI. Use `conda-forge <https://anaconda.org/conda-forge/structuralgt>`__ or the main GitHub branch for the API version, and the `GUI branch <https://github.com/compass-stc/StructuralGT/tree/DicksonOwuor-GUI>`__ for the GUI version.

Installation guide
==================
**StructuralGT** (API version only) is available on conda-forge for the *linux-64*, *osx-64*, and *win-64*
platforms. Install with

.. code:: bash

   conda install conda-forge::structuralgt

**StructuralGT** can also be built from source, via the
`public repository <https://github.com/compass-stc/StructuralGT>`__.
Prior to install, you will need to install some dependencies into your conda
environment. Note that installation will most likely be
successful if carried out in a new conda environment. While it is posisble to
obtain some of these dependencies with pip, installation will most likely be
sucessful when all dependencies are obtained with conda.

.. code:: bash

   git clone https://github.com/compass-stc/StructuralGT.git
   conda install -c conda-forge numpy scipy scikit-image matplotlib networkx opencv pandas gsd python-igraph pytest ipywidgets freud eigen cython igraph
   cd StructuralGT
   python3 setup.py build_ext
   python3 -m pip install . --no-deps

Alternatively, if building from source gives errors related to igraph, you can
build a python-only version of StructuralGT that skips compiling some of the
C modules used for fast calculations (AverageNodalConnectivity and
Betweenness).

.. code:: bash

   git clone https://github.com/compass-stc/StructuralGT.git
   conda install -c conda-forge numpy scipy scikit-image matplotlib networkx opencv pandas gsd python-igraph pytest ipywidgets freud igraph cython eigen
   cd StructuralGT
   export C_FLAG=FALSE
   python3 -m pip install . --no-deps


You can verify successful installation by installing pytest and running the
included tests:

.. code:: bash

   conda install pytest
   pytest

Quickstart and examples repository
==================================

To showcase the API, here is a simple example script used to predict the sheet resistance of silver nanowires, used in our recent publication :cite:`WuKadar2025`
To learn how to implement this yourself, consult our
`examples repository <https://github.com/compass-stc/StructuralGT-Examples>`__.

.. code:: python

   from StructuralGT.electronic import Electronic
   from StructuralGT.networks import Network

   agnwn_options = {"Thresh_method": 0, "gamma": 1.001, "md_filter": 0,
                    "g_blur":0, "autolvl": 0, "fg_color": 0, "laplacian": 0,
                    "scharr": 0, "sobel": 0, "lowpass": 0, "asize": 3,
                    "bsize": 1, "wsize": 1, "thresh": 128.0}

   AgNWN = Network('AgNWN')
   AgNWN.binarize(options=agnwn_options)
   AgNWN.img_to_skel()
   AgNWN.set_graph(weight_type= ['FixedWidthConductance'])

   width = AgNWN.image.shape[0]
   elec_properties = Electronic()
   elec_properties.compute(AgNWN, 0, 0, [[0,50],[width-50, width]])

Documentation
=============
To extend the above examples to novel analysis in your own work, you should
consult our `documentation <https://structuralgt.readthedocs.io/>`__.
You can also build the documentation from source, which requires the following dependencies:

- `Sphinx <http://www.sphinx-doc.org/>`_
- `The furo Sphinx Theme <https://pradyunsg.me/furo/>`_
- `nbsphinx <https://nbsphinx.readthedocs.io/>`_
- `jupyter_sphinx <https://jupyter-sphinx.readthedocs.io/>`_
- `sphinxcontrib-bibtex <https://sphinxcontrib-bibtex.readthedocs.io/>`_

You can install these dependencies using conda:

.. code-block:: bash

    conda install -c conda-forge sphinx furo nbsphinx jupyter_sphinx sphinxcontrib-bibtex

or pip:

.. code-block:: bash

    pip install sphinx sphinx-rtd-theme nbsphinx jupyter-sphinx sphinxcontrib-bibtex

To build the documentation, run the following commands in the source directory:

.. code-block:: bash

    cd doc
    make html
    # Then open build/html/index.html
.. code:: bash

   conda install sphinx furo nbsphinx jupyter_sphinx sphinxcontrib-bibtex sphinx-copybutton
   sphinx-build -b html doc html
