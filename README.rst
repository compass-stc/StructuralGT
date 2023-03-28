=================
StructuralGTEdits
=================

Overview
========
A python package for the extraction and analysis of graphs from 2D and 3D experimental micrographs. Image processing techniques taken from `StructuralGT <https://github.com/drewvecchio/StructuralGT>`__.

Use
===
To use, clone, build, and install from the `GitHub repository
<https://github.com/AlainKadar/StructuralGTEdits>`__.

.. code:: bash

   git clone https://github.com/AlainKadar/StructuralGTEdits
   cd StructuralGTEdits
   python setup.py install

Example
=======
The following minimal example shows how the package can be used to calculate the graph theoretic parameters of a 3D structural nanofibre network:

.. code:: python

   from StructuralGTEdits import network

   Nanofibre3DNetwork = network.StructuralNetwork('Nanofibre_Image_Stack')
   Nanofibre3DNetwork.binarize()
   Nanofibre3DNetwork.stack_to_gsd(crop=[0,500,0,500,0,500])
   Nanofibre3DNetwork.node_calc(betweenness=True)
   Nanofibre3DNetwork.node_labelling(Nanofibre3DNetwork.betweenness)
