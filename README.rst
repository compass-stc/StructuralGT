============
StructuralGT
============

Overview
========
A python package for the extraction and analysis of graphs from 2D and 3D experimental micrographs. Image processing techniques taken from `StructuralGT <https://github.com/drewvecchio/StructuralGT>`__.

Installation
============
StructuralGT is easiest to from source, using conda to link dependencies.
To do so, clone, build, 
and install from the `GitHub repository
<https://github.com/AlainKadar/StructuralGT>`__.
You will need to install the cython, igraph, and eigen. 

.. code:: bash

   git clone https://github.com/AlainKadar/StructuralGT
   conda install -c conda-forge igraph eigen cython
   cd StructuralGT
   python setup.py install

A conda installation streamlines linking the required dependencies. To avoid 
using conda, please see the documentation for a more customized installation.

Example
=======
The following minimal example shows how the package can be used to calculate the graph theoretic parameters of a 3D structural nanofibre network:

.. code:: python

   from StructuralGT.structural import Structural
   from StructuralGT.networks import Network

   Nanofibre3DNetwork = Network('Nanofibre_Image_Stack')
   Nanofibre3DNetwork.binarize()
   Nanofibre3DNetwork.img_to_skel(crop=[0,500,0,500,0,500])
   Nanofibre3DNetwork.set_graph(weight_type=['Length'])

   S = Structural()
   S.compute(Nanofibre3DNetwork)
   print(S.diameter)
