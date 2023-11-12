"""GT_Params: Calculates and collates graph theory indices from
an input graph. Utilizes the NetworkX and GraphRicciCurvature
libraries of algorithms.

Copyright (C) 2021, The Regents of the University of Michigan.

This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

Contributers: Drew Vecchio, Samuel Mahler, Mark D. Hammig, Nicholas A. Kotov
Contact email: vecdrew@umich.edu
"""

#from __main__ import *
import networkx as nx
import igraph as ig
import pandas as pd
import numpy as np
from statistics import mean
from time import sleep
from networkx.algorithms.centrality import betweenness_centrality, closeness_centrality, eigenvector_centrality
from networkx.algorithms import average_node_connectivity, global_efficiency, clustering, average_clustering
from networkx.algorithms import degree_assortativity_coefficient
from networkx.algorithms.flow import maximum_flow
from networkx.algorithms.distance_measures import diameter, periphery
from networkx.algorithms.wiener import wiener_index
#from StructuralGT import settings


def run_GT_calcs(G, Do_kdist, Do_dia, Do_BCdist, Do_CCdist, Do_ECdist, \
                 Do_GD, Do_Eff, Do_clust, Do_ANC, Do_Ast, Do_WI, multigraph):

    # getting nodes and edges and defining variables for later use
    klist = [0]
    Tlist = [0]
    BCdist = [0]
    CCdist = [0]
    ECdist = [0]
    data_dict = {"x":[], "y":[]}

    if multigraph:
        Do_BCdist = 0
        Do_ECdist = 0
        Do_clust = 0

    nnum = int(G.vcount())
    enum = int(G.vcount())

    if Do_ANC | Do_dia:
        connected_graph = G.is_connected()


    data_dict["x"].append("Number of nodes")
    data_dict["y"].append(nnum)

    data_dict["x"].append("Number of edges")
    data_dict["y"].append(enum)

    # calculating parameters as requested

    # creating degree histogram
    if(Do_kdist == 1):
        klist1 = g.degree()
        ksum = 0
        klist = np.zeros(len(klist1))
        for j in range(len(klist1)):
            ksum += klist1[j]
            klist[j] = klist1[j]
        k = ksum/len(klist1)
        k = round(k, 5)
        data_dict["x"].append("Average degree")
        data_dict["y"].append(k)

    # calculating network diameter
    if(Do_dia ==1):
        if connected_graph:
            dia = g.diameter()
        else:
            dia = 'NaN'
        data_dict["x"].append("Network diameter")
        data_dict["y"].append(dia)


    # calculating graph density
    if(Do_GD == 1):
        GD = g.density()
        GD = round(GD, 5)
        data_dict["x"].append("Graph density")
        data_dict["y"].append(GD)


    # not available on igraph
    # calculating global efficiency
    #if (Do_Eff == 1):
    #    Eff = global_efficiency(G)
       #   Eff = round(Eff, 5)
       #         # data_dict["x"].append("Global efficiency")
       #         # data_dict["y"].append(Eff)
       #  
    #Extensive index; not available on igraph
    #if (Do_WI == 1):
    #    WI = wiener_index(G)
    #    WI = round(WI, 1)
    #   data_dict["x"].append("Wiener Index")
    #   data_dict["y"].append(WI)



    # calculating clustering coefficients
    # Local coefficient calculations have been removed
    if(Do_clust == 1):
        clust = G.transistivity_undirected()
        clust = round(clust, 5)
        data_dict["x"].append("Average clustering coefficient")
        data_dict["y"].append(clust)

    # ANC removed because it is its own function in base.py

    # calculating assortativity coefficient
    if (Do_Ast == 1):
        Ast = G.assortativity_degree()
        Ast = round(Ast, 5)
        data_dict["x"].append("Assortativity coefficient")
        data_dict["y"].append(Ast)


    # calculating betweenness centrality histogram
    if (Do_BCdist == 1):
        BCdist = G.betweenness()
        Bcent = np.mean(BCdist)
        Bcent = round(Bcent, 5)
        data_dict["x"].append("Average betweenness centrality")
        data_dict["y"].append(Bcent)


    # calculating closeness centrality
    if(Do_CCdist == 1):
        CCdist = G.closeness()        
        Ccent = np.mean(CCdist)
        Ccent = round(Ccent, 5)
        data_dict["x"].append("Average closeness centrality")
        data_dict["y"].append(Ccent)


    # calculating eigenvector centrality
    if(Do_ECdist == 1):
        ECdist = G.eigenvector_centrality()
        Ecent = np.mean(ECdist)
        Ecent = round(Ecent, 5)
        data_dict["x"].append("Average eigenvector centrality")
        data_dict["y"].append(Ecent)




    data = pd.DataFrame(data_dict)

    return data,# klist, Tlist, BCdist, CCdist, ECdist

def run_weighted_GT_calcs(G, Do_kdist, Do_BCdist, Do_CCdist, Do_ECdist, Do_ANC, Do_Ast, Do_WI, multigraph):

    # includes weight in the calculations
    klist = [0]
    BCdist = [0]
    CCdist = [0]
    ECdist = [0]
    if multigraph:
        Do_BCdist = 0
        Do_ECdist = 0
        Do_ANC = 0

    wdata_dict = {"x": [], "y": []}

    if Do_ANC:
        connected_graph = nx.is_connected(G)




    if(Do_kdist == 1):
        klist1 = nx.degree(G, weight='weight')
        ksum = 0
        klist = np.zeros(len(klist1))
        for j in range(len(klist1)):
            ksum += klist1[j]
            klist[j] = klist1[j]
        k = ksum/len(klist1)
        k = round(k, 5)
        wdata_dict["x"].append("Weighted average degree")
        wdata_dict["y"].append(k)


    if (Do_WI == 1):
        WI = wiener_index(G, weight='length')
        WI = round(WI, 1)
        wdata_dict["x"].append("Length-weighted Wiener Index")
        wdata_dict["y"].append(WI)


    if (Do_ANC == 1):
        if connected_graph:
            max_flow = float(0)
            p = periphery(G)
            q = len(p) - 1
            for s in range(0, q - 1):
                for t in range(s + 1, q):
                    flow_value = maximum_flow(G, p[s], p[t], capacity='weight')[0]
                    if (flow_value > max_flow):
                        max_flow = flow_value
            max_flow = round(max_flow, 5)
        else:
            max_flow = 'NaN'
        wdata_dict["x"].append("Max flow between periphery")
        wdata_dict["y"].append(max_flow)


    if (Do_Ast == 1):
        Ast = degree_assortativity_coefficient(G, weight = 'pixel width')
        Ast = round(Ast, 5)
        wdata_dict["x"].append("Weighted assortativity coefficient")
        wdata_dict["y"].append(Ast)


    if(Do_BCdist == 1):
        BCdist1 = betweenness_centrality(G, weight='weight')
        Bsum = 0
        BCdist = np.zeros(len(BCdist1))
        for j in range(len(BCdist1)):
            Bsum += BCdist1[j]
            BCdist[j] = BCdist1[j]
        Bcent = Bsum / len(BCdist1)
        Bcent = round(Bcent, 5)
        wdata_dict["x"].append("Width-weighted average betweenness centrality")
        wdata_dict["y"].append(Bcent)


    if(Do_CCdist == 1):
        CCdist1 = closeness_centrality(G, distance='length')
        Csum = 0
        CCdist = np.zeros(len(CCdist1))
        for j in range(len(CCdist1)):
            Csum += CCdist1[j]
            CCdist[j] = CCdist1[j]
        Ccent = Csum / len(CCdist1)
        Ccent = round(Ccent, 5)
        wdata_dict["x"].append("Length-weighted average closeness centrality")
        wdata_dict["y"].append(Ccent)


    if (Do_ECdist == 1):
        try:
            ECdist1 = eigenvector_centrality(G, max_iter=100, weight='weight')
        except:
            ECdist1 = eigenvector_centrality(G, max_iter=10000, weight='weight')
        Esum = 0
        ECdist = np.zeros(len(ECdist1))
        for j in range(len(ECdist1)):
            Esum += ECdist1[j]
            ECdist[j] = ECdist1[j]
        Ecent = Esum / len(ECdist1)
        Ecent = round(Ecent, 5)
        wdata_dict["x"].append("Width-weighted average eigenvector centrality")
        wdata_dict["y"].append(Ecent)


    wdata = pd.DataFrame(wdata_dict)

    return wdata, klist, BCdist, CCdist, ECdist
