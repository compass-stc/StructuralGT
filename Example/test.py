from StructuralGT import networks
import numpy as np
from StructuralGT.electronic import Electronic
from StructuralGT.structural import Structural

options = {"Thresh_method":0, "gamma": 3, "md_filter": 0, "g_blur": 1, 
            "autolvl": 0,"fg_color":0,"laplacian": 0, "scharr": 0, "sobel":0 ,
            "lowpass": 1, "asize":7, "bsize":3, "wsize":5, "thresh": 103}

ANF = networks.Network('ANF')
ANF.binarize(options_dict=options)
ANF.img_to_skel(crop=[200,300,200,300], rotate=45, merge_nodes=5, remove_objects=10)
ANF.set_graph(weight_type=['FixedWidthConductance'], rho_dim=1, R_j=12, sub=True)

S = Structural()
S.compute(ANF)
print(S.diameter)

E = Electronic()
E.compute(ANF, 0, 0, [[0,50],[350,400]])
print(E.effective_resistance)


print(ANF.graph.transitivity_undirected())
