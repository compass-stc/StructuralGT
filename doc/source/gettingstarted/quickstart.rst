==========
Quickstart
==========

Data Formats
============

Before any analysis, you must first ensure your network images are laid out in your directory appropriately. Network images may be either a single image from which you would like to extract a two-dimensional (2D) network `or` it may be a stack of 2D images which represent a three-dimensional (3D) network. Each material network (whether a single 2D image or a stack of 2D images) must be stored in it's own directory. Supported image formats include :code:`.tiff`, :code:`.jpeg`, :code:`.png`, :code:`.bmp`, :code:`.gif`. For 2D images, the directory should contain just one image file. For 3D data, the images must be stored as a stack of 2D images and all of which must be named with an identical prefix, followed by a 4 digit identification of its depth, e.g. :code:`slice0000.tiff`.

Binarizing
==========

The first step in extracting a graph involves binarizing your networked images. Let's say we are dealing with the image of the aramid nanofiber network examined in Figure 5 of the original StructuralGT publication :cite:`Vecchio2021`, and that we have stored it in a directory called :code:`ANF`. The image processing options available are summarized here too. Optimal values for these parameters are best identified through trial and error, which can be efficiently carried out with the aid of the :class:`Binarizer` class, which offers realtime binarization in e.g. a Jupyter Notebook:

.. code:: python

   from StructuralGT import Binarizer

   B = Binarizer('ANF/slice0000.tiff')
   B.binarize()

When you are finished, tick the :code:`Export` box and the current image processing options will be exported to the same directory as the image you are working with.

Analysis
========

After laying out your images and establishing optimal binarization parameters you can begin analysis. Instantiating the :class:`Network` class and  calling the :meth:`binarize` method is usually the first step. If your images have already been binarized, you don't need to call this again.

.. code:: python

   from StructuralGT.networks import Network

   ANF = Network('ANF')
   ANF.binarize()

The next step in analysis involves converting into the `skeleton`, which is a 1-pixel wide representation of the network, and is achieved by calling the :meth:`img_to_skel` method. This sets the :attr:`skeleton` attribute, which can be examined to predict the quality of our subsequent graph extraction:

.. code:: python

   import matplotlib.pyplot as plt

   ANF.img_to_skel()
   plt.imshow(ANF.skeleton)

The next step is to extract the graph from the skeleton, by calling the :meth:`set_graph` method. This sets the :attr:`graph` attribute. The graph retains information about the locations of nodes and edges, which we use for visualization later. To analyse the network, we need a Compute module. Here, we use the :code:`Structural` module. Compute modules all have a :meth:`compute` method which takes a :class:`Network` object as an argument populates the :class:`Compute` module with attributes which store the result.

.. code:: python

   from StructuralGT.structural import Structural

   ANF_Compute = Structural()
   ANF_Compute.compute(ANF)

   print(f"Graph diameter is {ANF_Compute.diameter}")

With the :attr:`graph` attribute set, we can also compute graph theoretic parameters using the methods offered by the :code:`igraph` library :cite:`Csardi2005`. Let's calculate and plot betweenness centrality to reproduce Figure 5a from :cite:`Vecchio2021`:

.. code:: python

   ANF.set_graph()
   betweenness = ANF.graph.betweenness()

   fig, ax = plt.subplots()
   ANF.plot(ax=ax, parameter=betweenness)

