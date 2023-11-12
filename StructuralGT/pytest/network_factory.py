from StructuralGT import networks
import numpy as np

import StructuralGT
_path = StructuralGT.__path__[0]

anf_options = {"Thresh_method":0, "gamma": 3, "md_filter": 0, "g_blur": 1, 
            "autolvl": 0,"fg_color":0,"laplacian": 0, "scharr": 0, "sobel":0 ,
            "lowpass": 1, "asize":7, "bsize":3, "wsize":5, "thresh": 103}

agnwn_options = {"Thresh_method":0, "gamma": 3, "md_filter": 0, "g_blur": 1, 
            "autolvl": 0,"fg_color":0,"laplacian": 0, "scharr": 0, "sobel":0 ,
            "lowpass": 1, "asize":7, "bsize":3, "wsize":5, "thresh": 103}

def fibrous(weight_type=None):
    ANF = networks.Network(_path  + '/pytest/data/ANF')
    ANF.binarize(options_dict=anf_options)
    ANF.img_to_skel(crop=[200,300,200,300, 1, 3])
    ANF.set_graph(sub=True, weight_type=weight_type)

    return ANF

def conductive():
    AgNWN = networks.Network(_path + '/pytest/data/AgNWN')
    AgNWN.binarize(options_dict=agnwn_options)
    AgNWN.img_to_skel(crop=[149, 868, 408, 1127], rotate=45)
    AgNWN.set_graph(weight_type=['FixedWidthConductance'], sub=True, R_j=10, rho_dim=2)

    return AgNWN

