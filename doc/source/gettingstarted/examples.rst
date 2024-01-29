========
Examples
========

Conductivities of silver nanowire films
=======================================

Predicting the conductivties of two-dimensional silver nanowire (Ag NW) films is a common use case for graph theory. In this example, we show how to predict the sheet resistance of a film that was reported in REF. To do this we must specify a conductance weight when we set the graph. We may optionally rotate the graph to investivate anisotropy, as well as include a resistance assocaited with NW junctions (see API).

.. code:: python

   from StructuralGT.electronic import Electronic
   from StructuralGT.networks import Network

   agnwn_options = {"Thresh_method": 0, "gamma": 1.001, "md_filter": 0,
                    "g_blur":0, "autolvl": 0, "fg_color": 0, "laplacian": 0,
                    "scharr": 0, "sobel": 0, "lowpass": 0, "asize": 3,
                    "bsize": 1, "wsize": 1, "thresh": 128.0}

   AgNWN = Network('AgNWN')
   AgNWN.binarize(options_dict=agnwn_options)
   AgNWN.img_to_skel()
   AgNWN.set_graph(weight_type= ['FixedWidthConductance'])

   width = AgNWN.image.shape[0]
   elec_properties = Electronic()
   elec_properties.compute(AgNWN, 0, 0, [[0,50],[width-50, width]])


Structural attributes of 3-dimensional tomography of aramid nanofibres
======================================================================
