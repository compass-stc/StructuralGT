from StructuralGT import networks
import numpy as np
import matplotlib.pyplot as plt

import StructuralGT
_path = StructuralGT.__path__[0]

anf_options = {"Thresh_method":0, "gamma": 3, "md_filter": 0, "g_blur": 1, 
            "autolvl": 0,"fg_color":0,"laplacian": 0, "scharr": 0, "sobel":0 ,
            "lowpass": 1, "asize":7, "bsize":3, "wsize":5, "thresh": 103}

agnwn_options = {"Thresh_method":0, "gamma": 3, "md_filter": 0, "g_blur": 1, 
            "autolvl": 0,"fg_color":0,"laplacian": 0, "scharr": 0, "sobel":0 ,
            "lowpass": 1, "asize":7, "bsize":3, "wsize":5, "thresh": 103}

stick_options = {"Thresh_method":0, "gamma": 2, "md_filter": 0, "g_blur": 0,"autolvl": 0,
               "fg_color":0,"laplacian": 0,"scharr": 0, "sobel": 1,"lowpass": 0, "asize": 11,
               "bsize": 11, "wsize": 10, "thresh": 93}

def fibrous(weight_type=None):
    ANF = networks.Network(_path  + '/pytest/data/ANF')
    ANF.binarize(options=anf_options)
    ANF.img_to_skel(crop=[200,300,200,300, 1, 3])
    ANF.set_graph(weight_type=weight_type)

    return ANF

def conductive():
    AgNWN = networks.Network(_path + '/pytest/data/AgNWN')
    AgNWN.binarize(options=agnwn_options)
    AgNWN.img_to_skel(crop=[149, 868, 408, 1127], rotate=45)
    AgNWN.set_graph(weight_type=['FixedWidthConductance'], R_j=10, rho_dim=2)

    return AgNWN

def random_stick(aligned=True):

    def draw_stick(ax, x, y, length, angle, size):
        if aligned: angle=0
        x_end = x + length * np.cos(angle)
        y_end = y + length * np.sin(angle)
        if x_end > size and y_end < size:
            y_mid = y + (size - x) * np.tan(angle)
            ax.plot([x, size], [y, y_mid], 'w-', linewidth=1.2)
            ax.plot([0, length*np.cos(angle)-size+x], [y_mid, y_end], 'w-', linewidth=1.2)
        elif x_end < size and y_end > size:
            x_mid = x + (size - y) / np.tan(angle)
            ax.plot([x, x_mid], [y, size], 'w-', linewidth=1.2)
            ax.plot([x_mid, x_end], [0, length*np.sin(angle)-size+y], 'w-', linewidth=1.2)
        elif x_end > size and y_end > size:
            x_mid = x + (size - y) / np.tan(angle)
            y_mid = y + (size - x) * np.tan(angle)
            if y_mid > size:
                ax.plot([x, x_mid], [y, size], 'w-', linewidth=1.2)
                ax.plot([x_mid,size], [0, y_mid-size], 'w-', linewidth=1.2)
                ax.plot([0, length*np.cos(angle)-size+x], [y_mid-size, length*np.sin(angle)-size+y], 'w-', linewidth=1.2)
            if x_mid > size:
                ax.plot([x, size], [y, y_mid], 'w-', linewidth=1.2)
                ax.plot([0, x_mid-size], [y_mid, size], 'w-', linewidth=1.2)
                ax.plot([x_mid-size, length*np.cos(angle)-size+x], [0, length*np.sin(angle)-size+y], 'w-', linewidth=1.2)
        else:
            ax.plot([x, x_end], [y, y_end], 'w-', linewidth=1.2)

    def main(num_sticks=210, stick_length=300.0):
        # Square size
        size = 1000

        fig, ax = plt.subplots()
        ax.set_xlim(0, size)
        ax.set_ylim(0, size)
        ax.set_facecolor('black')
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])
        for _ in range(num_sticks):
            x_start = np.random.uniform(0, size)
            y_start = np.random.uniform(0, size)
            angle = np.random.uniform(0, 2 * np.pi)  
        
        draw_stick(ax, x_start, y_start, stick_length, angle, size)

        return fig

    fig = main()
    if aligned:
        img_path = _path + '/pytest/data/Aligned'
    else:
        img_path = _path + '/pytest/data/Random'
    fig.savefig(img_path + '/slice0000.png',bbox_inches='tight', dpi=300)

    RS = networks.Network(img_path)
    RS.binarize(options=stick_options)
    RS.img_to_skel()
    RS.set_graph(sub=False)

    return RS
