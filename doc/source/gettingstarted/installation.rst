============
Installation
============

Installing with conda
=====================
TODO

Compiling from source
=====================
StructuralGT can also be compiled from source.

Linking dependencies with conda
-------------------------------
When compiling from source, dependencies are easiest to link with conda.
To do so, clone, build, 
and install from the `GitHub repository
<https://github.com/AlainKadar/StructuralGT>`__.
You will need to install cython, igraph, and eigen. 

.. code:: bash

   git clone https://github.com/AlainKadar/StructuralGT
   conda install -c conda-forge igraph eigen cython
   cd StructuralGT
   python setup.py install

.. _installation-label:
Linking dependencies without conda
----------------------------------
TODO

Documentation
=============

The following are **required** for building **StructuralGT** documentation:

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
