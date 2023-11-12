==========
Quickstart
==========

Data Formats
============

Before any analysis, you must first ensure your network images are laid out in your directory appropriately. Network images may be either a single image from which you would like to extract a two-dimensional (2D) network `or` it may be a stack of 2D images which represent a three-dimensional (3D) network. The rules for laying them out in storage are the same for both cases.  Namely, each material network (whether a single 2D image or a stack of 2D images) must be stored in it's own directory. Supported image formats include REF. The name of each image in the directory should be :code:`slice` followed by a 4 number identification of its depth. Therefore, single images will be named :code:`slice0000`, followed by the filetype. TODO remove this requirement.

Binarizing
==========

The first step in extracting a graph involves binarizing your networked images. Let's say we are dealing with the image of the aramid nanofiber network examined in Figure 5 of the original StructuralGT publication:cite:`Vecchio2021`, and that we have stored it in a directory called :code:`ANF`. The image processing options available are summarized in :cite:`Vecchio2021`. Optimal values for these parameters are best identified through trial and error, which can be efficiently carried out with the aid of the :class:`Binarizer` class, which offers realtime binarization in e.g. a Jupyter Notebook:

.. code:: python

   from StructuralGT import Binarizer

   Binarizer('ANF')


Analysis
========

After laying out your images and establishing optimal binarization parameters you can begin analysis. Instantiating a :class:`Network` class and  calling the :meth:`binarize` method is usually the first step. In this example, we use the :class:`StructuralNetwork` class:

.. code:: python

   from StructuralGT import physical_networks

   ANF = physical_networks.StructuralNetwork('ANF')
   ANF.binarize()

The next step in analysis involves converting into the `skeleton`, which is a 1-pixel wide representation of the network, and is achieved by calling the :meth:`img_to_skel` method. This sets the :attr:`skeleton` attribute, which can be examined to predict the quality of our subsequent graph extraction:

.. code:: python

   import matplotlib.pyplot as plt

   ANF.img_to_skel()
   plt.imshow(ANF.skeleton)

Finally, we extract the graph from the skeleton, by calling the :meth:`set_graph` method. This sets the :attr:`graph` attribute. The graph retains information about the locations of nodes and edges, which we use for visualization later. With the :attr:`graph` attribute set, we can compute graph theoretic parameters using the methods offered by the :code:`igraph` library:cite:`Csardi2005`. Let's calculate and plot betweenness centrality to reproduce Figure 5a from :cite:`Vecchio2021`:

.. code:: python

   ANF.set_graph()
   betweenness = ANF.graph.betweenness()

   fig, ax = plt.subplots()
   ANF.plot(ax=ax, parameter=betweenness)


