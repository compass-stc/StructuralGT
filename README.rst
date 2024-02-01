============
StructuralGT
============

Overview
========
A python package for the extraction and analysis of graphs from 2D and 3D experimental micrographs. Image processing techniques taken from `StructuralGT <https://github.com/drewvecchio/StructuralGT>`__.

Use
===
To use, clone, build, and install from the `GitHub repository
<https://github.com/AlainKadar/StructuralGT>`__. You will need to install the cython, igraph, and eigen with conda.

.. code:: bash

   conda install igraph eigen cython
   git clone https://github.com/AlainKadar/StructuralGT
   cd StructuralGT
   python setup.py install

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
   S.compute(ANF)
   print(S.diameter)
