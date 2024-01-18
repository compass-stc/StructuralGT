========
Examples
========

Conductivities of silver nanowire films
=======================================

Predicting the conductivties of two-dimensional silver nanowire (Ag NW) films is a common use case for graph theory. In this example, we show how to predict the sheet resistance of a film that was reported in REF. To do this we must specify a conductance weight type in the :code:`Compute` module and weighting method in the :meth:`set_graph` method.

.. code:: python

   from StructuralGT.electronic import Electronic
   from StructuralGT.networks import Network

agnwn_options = {"Thresh_method":0, "gamma": 3, "md_filter": 0, "g_blur": 1, 
            "autolvl": 0,"fg_color":0,"laplacian": 0, "scharr": 0, "sobel":0 ,
            "lowpass": 1, "asize":7, "bsize":3, "wsize":5, "thresh": 103}
   AgNWN = Network('AgNWN')
   AgNWN.binarize(options_dict=agnwn_options)

   elec_properties = Electronic(weight_typ)
   elec_properties.compute()
