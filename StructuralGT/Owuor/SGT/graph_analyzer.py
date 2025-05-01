# SPDX-License-Identifier: GNU GPL v3

"""
Compute graph theory metrics
"""

import os
import math
import datetime
import itertools
import multiprocessing
import numpy as np
import scipy as sp
import pandas as pd
import networkx as nx
import matplotlib.table as tbl
import matplotlib.pyplot as plt
from cv2.typing import MatLike
from statistics import stdev, StatisticsError

from networkx.algorithms.centrality import betweenness_centrality, closeness_centrality
from networkx.algorithms.centrality import eigenvector_centrality, percolation_centrality
from networkx.algorithms import average_node_connectivity, global_efficiency, clustering
from networkx.algorithms import degree_assortativity_coefficient
from networkx.algorithms.flow import maximum_flow
from networkx.algorithms.distance_measures import diameter, periphery
from networkx.algorithms.wiener import wiener_index

from .progress_update import ProgressUpdate
from .fiber_network import FiberNetworkBuilder
from .network_processor import NetworkProcessor

import sgt_c_module as sgt
from .sgt_utils import get_num_cores
from ..configs.config_loader import load_gtc_configs


class GraphAnalyzer(ProgressUpdate):
    """
    A class that computes all the user-selected graph theory metrics and writes the results in a PDF file.

    Args:
        ntwk_p: Network Processor object.
        allow_multiprocessing: a decision to allow multiprocessing computing.
    """

    def __init__(self, ntwk_p: NetworkProcessor, allow_multiprocessing: bool = True):
        """
        A class that computes all the user-selected graph theory metrics and writes the results in a PDF file.

        :param ntwk_p: Network Processor object.
        :param allow_multiprocessing: Allows multiprocessing computing.

        >>> i_path = "path/to/image"
        >>> o_dir = ""
        >>>
        >>> ntwk_obj = NetworkProcessor(i_path, o_dir)
        >>> metrics_obj = GraphAnalyzer(ntwk_obj)
        >>> metrics_obj.run_analyzer()
        """
        super(GraphAnalyzer, self).__init__()
        self.configs: dict = load_gtc_configs()  # graph theory computation parameters and options.
        self.allow_mp: bool = allow_multiprocessing
        self.ntwk_p: NetworkProcessor = ntwk_p
        self.plot_figures: list | None = None
        self.output_data: pd.DataFrame | None = None
        self.weighted_output_data: pd.DataFrame | None = None
        self.histogram_data = {"degree_distribution": [0], "clustering_coefficients": [0],
                               "betweenness_distribution": [0], "closeness_distribution": [0],
                               "eigenvector_distribution": [0], "ohms_distribution": [0],
                               "percolation_distribution": [], "weighted_degree_distribution": [0],
                               "weighted_clustering_coefficients": [0], "weighted_betweenness_distribution": [0],
                               "currentflow_distribution": [0], "weighted_closeness_distribution": [0],
                               "weighted_eigenvector_distribution": [0], "weighted_percolation_distribution": [0]}

    def track_img_progress(self, value, msg):
        self.update_status([value, msg])

    def run_analyzer(self):
        """
            Execute functions that will process image filters and extract the graph from the processed image
        """

        # 1. Get graph extracted from selected images
        sel_batch = self.ntwk_p.get_selected_batch()
        graph_obj = sel_batch.graph_obj

        # 2. Apply image filters and extract the graph (only if it has not been executed)
        if graph_obj is None:
            self.ntwk_p.add_listener(self.track_img_progress)
            self.ntwk_p.apply_img_filters()                     # Apply image filters
            self.ntwk_p.build_graph_network()                   # Extract graph from binary image
            self.ntwk_p.remove_listener(self.track_img_progress)
            self.abort = self.ntwk_p.abort
            self.update_status([100, "Graph successfully extracted!"]) if not self.abort else None
            sel_batch = self.ntwk_p.get_selected_batch()
            graph_obj = sel_batch.graph_obj

        if self.abort:
            return

        # 3. Compute Unweighted GT parameters
        self.output_data = self.compute_gt_metrics(graph_obj)

        if self.abort:
            self.update_status([-1, "Problem encountered while computing un-weighted GT parameters."])
            return

        # 4. Compute Weighted GT parameters (skip if MultiGraph)
        self.weighted_output_data = self.compute_weighted_gt_metrics(graph_obj)

        if self.abort:
            self.update_status([-1, "Problem encountered while computing weighted GT parameters."])
            return

        # 5. Generate results in PDF
        self.plot_figures = self.generate_pdf_output(graph_obj)

    def compute_gt_metrics(self, graph_obj: FiberNetworkBuilder = None):
        """
        Compute unweighted graph theory metrics.

        :param graph_obj: GraphExtractor object.

        :return: A Pandas DataFrame containing the unweighted graph theory metrics.
        """

        if graph_obj is None:
            return None

        self.update_status([1, "Performing un-weighted analysis..."])

        graph = graph_obj.nx_3d_graph
        opt_gtc = self.configs
        data_dict = {"x": [], "y": []}

        node_count = int(nx.number_of_nodes(graph))
        edge_count = int(nx.number_of_edges(graph))

        data_dict["x"].append("Number of nodes")
        data_dict["y"].append(node_count)

        data_dict["x"].append("Number of edges")
        data_dict["y"].append(edge_count)

        # angle of edges (inbound and outbound)
        angle_arr = np.array(list(nx.get_edge_attributes(graph, 'angle').values()))
        data_dict["x"].append('Average edge angle (degrees)')
        data_dict["y"].append(round(np.average(angle_arr), 3))

        data_dict["x"].append('Median edge angle (degrees)')
        data_dict["y"].append(round(np.median(angle_arr), 3))

        if graph.number_of_nodes() <= 0:
            self.update_status([-1, "Problem with graph (change filter and graph options)."])
            return None

        # creating degree histogram
        if opt_gtc["display_degree_histogram"]["value"] == 1:
            self.update_status([5, "Computing graph degree..."])
            deg_distribution_1 = dict(nx.degree(graph))
            deg_distribution = np.array(list(deg_distribution_1.values()), dtype=float)
            hist_name = "degree_distribution"
            hist_label = "Average degree"
            data_dict = self._update_histogram_data(data_dict, deg_distribution, hist_name, hist_label)

        connected_graph = None
        if (opt_gtc["compute_network_diameter"]["value"] == 1) or (
                opt_gtc["compute_avg_node_connectivity"]["value"] == 1):
            try:
                connected_graph = nx.is_connected(graph)
            except nx.exception.NetworkXPointlessConcept:
                pass

        # calculating network diameter
        if opt_gtc["compute_network_diameter"]["value"] == 1:
            self.update_status([10, "Computing network diameter..."])
            if connected_graph:
                dia = int(diameter(graph))
            else:
                dia = 'NaN'
            data_dict["x"].append("Network diameter")
            data_dict["y"].append(dia)

        # calculating average nodal connectivity
        if opt_gtc["compute_avg_node_connectivity"]["value"] == 1:
            if self.abort:
                self.update_status([-1, "Task aborted."])
                return None
            self.update_status([15, "Computing node connectivity..."])
            if connected_graph:
                # use_igraph = opt_gtc["compute_lang == 'C'"]["value"]
                use_igraph = True
                if use_igraph:
                    # use iGraph Lib in C
                    self.update_status([15, "Using iGraph library..."])
                    avg_node_con = self.igraph_average_node_connectivity(graph_obj)
                else:
                    # Use NetworkX Lib in Python
                    self.update_status([15, "Using NetworkX library..."])
                    if self.allow_mp:  # Multi-processing
                        avg_node_con = self.average_node_connectivity(graph_obj)
                    else:
                        avg_node_con = average_node_connectivity(graph)
                avg_node_con = round(avg_node_con, 5)
            else:
                avg_node_con = 'NaN'
            data_dict["x"].append("Average node connectivity")
            data_dict["y"].append(avg_node_con)

        # calculating graph density
        if opt_gtc["compute_graph_density"]["value"] == 1:
            self.update_status([20, "Computing graph density..."])
            g_density = nx.density(graph)
            g_density = round(g_density, 5)
            data_dict["x"].append("Graph density")
            data_dict["y"].append(g_density)

        # calculating global efficiency
        if opt_gtc["compute_global_efficiency"]["value"] == 1:
            if self.abort:
                self.update_status([-1, "Task aborted."])
                return None
            self.update_status([25, "Computing global efficiency..."])
            g_eff = global_efficiency(graph)
            g_eff = round(g_eff, 5)
            data_dict["x"].append("Global efficiency")
            data_dict["y"].append(g_eff)

        if opt_gtc["compute_wiener_index"]["value"] == 1:
            self.update_status([30, "Computing wiener index..."])
            # settings.update_label("Calculating w_index...")
            w_index = wiener_index(graph)
            w_index = round(w_index, 1)
            data_dict["x"].append("Wiener Index")
            data_dict["y"].append(w_index)

        # calculating assortativity coefficient
        if opt_gtc["compute_assortativity_coef"]["value"] == 1:
            self.update_status([35, "Computing assortativity coefficient..."])
            a_coef = degree_assortativity_coefficient(graph)
            a_coef = round(a_coef, 5)
            data_dict["x"].append("Assortativity coefficient")
            data_dict["y"].append(a_coef)

        # calculating clustering coefficients
        if opt_gtc["compute_avg_clustering_coef"]["value"] == 1:
            self.update_status([40, "Computing clustering coefficients..."])
            coefficients_1 = clustering(graph)
            cl_coefficients = np.array(list(coefficients_1.values()), dtype=float)
            hist_name = "clustering_coefficients"
            hist_label = "Average clustering coefficient"
            data_dict = self._update_histogram_data(data_dict, cl_coefficients, hist_name, hist_label)

        # calculating betweenness centrality histogram
        if opt_gtc["display_betweenness_centrality_histogram"]["value"] == 1:
            self.update_status([45, "Computing betweenness centrality..."])
            b_distribution_1 = betweenness_centrality(graph)
            b_distribution = np.array(list(b_distribution_1.values()), dtype=float)
            hist_name = "betweenness_distribution"
            hist_label = "Average betweenness centrality"
            data_dict = self._update_histogram_data(data_dict, b_distribution, hist_name, hist_label)

        # calculating eigenvector centrality
        if opt_gtc["display_eigenvector_centrality_histogram"]["value"] == 1:
            self.update_status([50, "Computing eigenvector centrality..."])
            try:
                e_vecs_1 = eigenvector_centrality(graph, max_iter=100)
            except nx.exception.PowerIterationFailedConvergence:
                e_vecs_1 = eigenvector_centrality(graph, max_iter=10000)
            e_vecs = np.array(list(e_vecs_1.values()), dtype=float)
            hist_name = "eigenvector_distribution"
            hist_label = "Average eigenvector centrality"
            data_dict = self._update_histogram_data(data_dict, e_vecs, hist_name, hist_label)

        # calculating closeness centrality
        if opt_gtc["display_closeness_centrality_histogram"]["value"] == 1:
            self.update_status([55, "Computing closeness centrality..."])
            close_distribution_1 = closeness_centrality(graph)
            close_distribution = np.array(list(close_distribution_1.values()), dtype=float)
            hist_name = "closeness_distribution"
            hist_label = "Average closeness centrality"
            data_dict = self._update_histogram_data(data_dict, close_distribution, hist_name, hist_label)

        # calculating Ohms centrality
        if opt_gtc["display_ohms_histogram"]["value"] == 1:
            self.update_status([60, "Computing Ohms centrality..."])
            o_distribution_1, res = self.compute_ohms_centrality(graph_obj)
            o_distribution = np.array(list(o_distribution_1.values()), dtype=float)
            hist_name = "ohms_distribution"
            hist_label = "Average Ohms centrality"
            data_dict = self._update_histogram_data(data_dict, o_distribution, hist_name, hist_label)
            data_dict["x"].append("Ohms centrality (avg. area)")
            data_dict["y"].append(f"{res['avg area']} " + r"$m^2$")
            data_dict["x"].append("Ohms centrality (avg. length)")
            data_dict["y"].append(f"{res['avg length']} m")
            data_dict["x"].append("Ohms centrality (avg. width)")
            data_dict["y"].append(f"{res['avg width']} m")
            data_dict["x"].append("Ohms centrality (g shape coeff.)")
            data_dict["y"].append(f"{res['g shape']}")
            data_dict["x"].append("Ohms centrality (conductivity)")
            data_dict["y"].append(f"{res['conductivity']} S/m")

            # calculating current-flow betweenness centrality
        """
        if opt_gtc["display_current_flow_betweenness_centrality_histogram"]["value"] == 1:
            # We select source nodes and target nodes with highest degree-centrality

            gph = self.g_obj.nx_connected_graph
            all_nodes = list(gph.nodes())
            # source_nodes = random.sample(all_nodes, k=5)
            # rem_nodes = list(set(source_nodes) - set(source_nodes))
            # target_nodes = random.sample(rem_nodes, k=5)
            degree_centrality = nx.degree_centrality(gph)
            sorted_nodes = sorted(all_nodes, key=lambda x: degree_centrality[x], reverse=True)
            source_nodes = sorted_nodes[:5]
            target_nodes = sorted_nodes[-5:]

            self.update_status([62, "Computing current-flow betweenness centrality..."])
            cf_distribution_1 = nx.current_flow_betweenness_centrality_subset(gph, source_nodes, target_nodes)
            cf_distribution = np.array(list(cf_distribution_1.values()), dtype=float)
            hist_name = "currentflow_distribution"
            hist_label = "Average current-flow betweenness centrality"
            data_dict = self.update_histogram_data(data_dict, cf_distribution, hist_name, hist_label)
        """

        # calculating percolation centrality
        if opt_gtc["display_percolation_histogram"]["value"] == 1:
            self.update_status([65, "Computing percolation centrality..."])
            p_distribution_1 = percolation_centrality(graph, states=None)
            p_distribution = np.array(list(p_distribution_1.values()), dtype=float)
            hist_name = "percolation_distribution"
            hist_label = "Average percolation centrality"
            data_dict = self._update_histogram_data(data_dict, p_distribution, hist_name, hist_label)

        return pd.DataFrame(data_dict)

    def compute_weighted_gt_metrics(self, graph_obj: FiberNetworkBuilder = None):
        """
        Compute weighted graph theory metrics.

        :param graph_obj: GraphExtractor object.

        :return: A Pandas DataFrame containing the weighted graph theory metrics.
        """
        if graph_obj is None:
            return None

        if not graph_obj.configs["has_weights"]["value"]:
            return None

        self.update_status([70, "Performing weighted analysis..."])

        graph = graph_obj.nx_3d_graph
        opt_gtc = self.configs
        wt_type = graph_obj.get_weight_type()
        weight_type = FiberNetworkBuilder.get_weight_options().get(wt_type)
        data_dict = {"x": [], "y": []}

        if graph.number_of_nodes() <= 0:
            self.update_status([-1, "Problem with graph (change filter and graph options)."])
            return None

        if opt_gtc["display_degree_histogram"]["value"] == 1:
            self.update_status([72, "Compute weighted graph degree..."])
            deg_distribution_1 = dict(nx.degree(graph, weight='weight'))
            deg_distribution = np.array(list(deg_distribution_1.values()), dtype=float)
            hist_name = "weighted_degree_distribution"
            hist_label = f"{weight_type}-weighted average degree"
            data_dict = self._update_histogram_data(data_dict, deg_distribution, hist_name, hist_label)

        if opt_gtc["compute_wiener_index"]["value"] == 1:
            self.update_status([74, "Compute weighted wiener index..."])
            w_index = wiener_index(graph, weight='length')
            w_index = round(w_index, 1)
            data_dict["x"].append("Length-weighted Wiener Index")
            data_dict["y"].append(w_index)

        if opt_gtc["compute_avg_node_connectivity"]["value"] == 1:
            self.update_status([76, "Compute weighted node connectivity..."])
            connected_graph = nx.is_connected(graph)
            if connected_graph:
                max_flow = float(0)
                p = periphery(graph)
                q = len(p) - 1
                for s in range(0, q - 1):
                    for t in range(s + 1, q):
                        flow_value = maximum_flow(graph, p[s], p[t], capacity='weight')[0]
                        if flow_value > max_flow:
                            max_flow = flow_value
                max_flow = round(max_flow, 5)
            else:
                max_flow = 'NaN'
            data_dict["x"].append("Max flow between periphery")
            data_dict["y"].append(max_flow)

        if opt_gtc["compute_assortativity_coef"]["value"] == 1:
            self.update_status([78, "Compute weighted assortativity..."])
            a_coef = degree_assortativity_coefficient(graph, weight='width')
            a_coef = round(a_coef, 5)
            data_dict["x"].append("Width-weighted assortativity coefficient")
            data_dict["y"].append(a_coef)

        if opt_gtc["display_betweenness_centrality_histogram"]["value"] == 1:
            self.update_status([80, "Compute weighted betweenness centrality..."])
            b_distribution_1 = betweenness_centrality(graph, weight='weight')
            b_distribution = np.array(list(b_distribution_1.values()), dtype=float)
            hist_name = "weighted_betweenness_distribution"
            hist_label = f"{weight_type}-weighted average betweenness centrality"
            data_dict = self._update_histogram_data(data_dict, b_distribution, hist_name, hist_label)

        if opt_gtc["display_closeness_centrality_histogram"]["value"] == 1:
            self.update_status([82, "Compute weighted closeness centrality..."])
            close_distribution_1 = closeness_centrality(graph, distance='length')
            close_distribution = np.array(list(close_distribution_1.values()), dtype=float)
            hist_name = "weighted_closeness_distribution"
            hist_label = f"Length-weighted average closeness centrality"
            data_dict = self._update_histogram_data(data_dict, close_distribution, hist_name, hist_label)

        if opt_gtc["display_eigenvector_centrality_histogram"]["value"] == 1:
            if self.abort:
                self.update_status([-1, "Task aborted."])
                return None
            self.update_status([84, "Compute weighted eigenvector centrality..."])
            try:
                e_vecs_1 = eigenvector_centrality(graph, max_iter=100, weight='weight')
            except nx.exception.PowerIterationFailedConvergence:
                e_vecs_1 = eigenvector_centrality(graph, max_iter=10000, weight='weight')
            e_vecs = np.array(list(e_vecs_1.values()), dtype=float)
            hist_name = "weighted_eigenvector_distribution"
            hist_label = f"{weight_type}-weighted average eigenvector centrality"
            data_dict = self._update_histogram_data(data_dict, e_vecs, hist_name, hist_label)

        if opt_gtc["display_percolation_histogram"]["value"] == 1:
            self.update_status([86, "Compute weighted percolation centrality..."])
            p_distribution_1 = percolation_centrality(graph, states=None, weight='weight')
            p_distribution = np.array(list(p_distribution_1.values()), dtype=float)
            hist_name = "weighted_percolation_distribution"
            hist_label = f"{weight_type}-weighted average percolation centrality"
            data_dict = self._update_histogram_data(data_dict, p_distribution, hist_name, hist_label)

        # calculate cross-sectional area of edges
        wt_type = graph_obj.get_weight_type()
        if wt_type == 'AREA':
            self.update_status([68, "Computing average (edge) cross-sectional area..."])
            temp_distribution = []
            for (s, e) in graph.edges():
                temp_distribution.append(graph[s][e]['weight'])
            a_distribution = np.array(temp_distribution, dtype=float)
            ae_val = np.average(a_distribution)
            ae_val = round(ae_val, 5)
            data_dict["x"].append(f"Average edge cross-sectional area (nm\u00b2)")
            data_dict["y"].append(ae_val)

        return pd.DataFrame(data_dict)

    def compute_ohms_centrality(self, graph_obj: FiberNetworkBuilder):
        r"""
        Computes Ohms centrality value for each node based on actual pixel width and length of edges in meters.

        :param graph_obj: Graph extractor object.

        Returns: Ohms centrality distribution
        """
        ohms_dict = {}
        lst_area = []
        lst_len = []
        lst_width = []
        nx_graph = graph_obj.nx_3d_graph

        sel_batch = self.ntwk_p.get_selected_batch()
        sel_images = self.ntwk_p.get_selected_images(sel_batch)
        px_sizes = np.array([img.configs["pixel_width"]["value"] for img in sel_images])
        rho_dims = np.array([img.configs["resistivity"]["value"] for img in sel_images])

        px_size = float(np.average(px_sizes.astype(float)))
        rho_dim = float(np.average(rho_dims.astype(float)))
        pixel_dim = px_size  # * (10 ** 9)  # Convert to nanometers
        g_shape = 1

        b_dict = betweenness_centrality(nx_graph)
        lst_nodes = list(nx_graph.nodes())
        for n in lst_nodes:
            # compute Ohms centrality value for each node
            b_val = float(b_dict[n])
            if b_val == 0:
                ohms_val = 0
            else:
                connected_nodes = nx_graph[n]  # all nodes connected to node n
                arr_len = []
                arr_dia = []
                for idx, val in connected_nodes.items():
                    arr_len.append(val['length'])
                    arr_dia.append(val['width'])
                arr_len = np.array(arr_len, dtype=float)
                arr_dia = np.array(arr_dia, dtype=float)

                pix_width = float(np.average(arr_dia))
                pix_length = np.sum(arr_len)
                length = pix_length * pixel_dim
                width = pix_width * pixel_dim
                # area = math.pi * 89.6 * (width * 0.5) ** 2
                area = g_shape * (width * width)
                ohms_val = ((b_val * length * rho_dim) / area)
                lst_len.append(length)
                lst_area.append(area)
                lst_width.append(width)
                # if n < 5:
            ohms_dict[n] = ohms_val
        avg_area = np.average(np.array(lst_area, dtype=float))
        avg_len = np.average(np.array(lst_len, dtype=float))
        avg_width = np.average(np.array(lst_width, dtype=float))
        res = {'avg area': avg_area, 'avg length': avg_len, 'avg width': avg_width,
               'g shape': g_shape, 'conductivity': round((1 / rho_dim), 2)}

        return ohms_dict, res

    def average_node_connectivity(self, graph_obj: FiberNetworkBuilder, flow_func=None):
        r"""Returns the average connectivity of a graph G.

        The average connectivity `\bar{\kappa}` of a graph G is the average
        of local node connectivity over all pairs of the nx_3d_graph nodes.

        https://networkx.org/documentation/stable/_modules/networkx/algorithms/connectivity/connectivity.html#average_node_connectivity

        Parameters
        ----------
        graph_obj: Graph extractor object.

        flow_func : function
            A function for computing the maximum flow among a pair of nodes.
            The function has to accept at least three parameters: a Digraph,
            a source node, and a target node. And return a residual network
            that follows NetworkX conventions (see: meth:`maximum_flow` for
            details). If flow_func is None, the default maximum flow function
            (:meth:`edmonds_karp`) is used. See :meth:`local_node_connectivity`
            for details. The choice of the default function may change from
            version to version and should not be relied on. Default value: None.

        Returns
        -------
        K : float
            Average node connectivity

        References
        ----------
        [1]  Beineke, L., O. Oellermann, and r_network. Pippert (2002). The average
                connectivity of a graph. Discrete mathematics 252(1-3), 31-45.
                https://www.sciencedirect.com/science/article/pii/S0012365X01001807

        """

        nx_graph = graph_obj.nx_3d_graph
        if nx_graph.is_directed():
            iter_func = itertools.permutations
        else:
            iter_func = itertools.combinations

        # Reuse the auxiliary digraph and the residual network
        a_digraph = nx.algorithms.connectivity.build_auxiliary_node_connectivity(nx_graph)
        r_network = nx.algorithms.flow.build_residual_network(a_digraph, "capacity")
        # kwargs = {"flow_func": flow_func, "auxiliary": a_digraph, "residual": r_network}

        num, den = 0, 0
        with multiprocessing.Pool() as pool:
            items = [(nx_graph, u, v, flow_func, a_digraph, r_network) for u, v in iter_func(nx_graph, 2)]
            for n in pool.starmap(nx.algorithms.connectivity.local_node_connectivity, items):
                num += n
                den += 1
                if self.abort:
                    self.update_status([-1, "Task aborted."])
                    return 0
        if den == 0:
            return 0
        return num / den

    def igraph_average_node_connectivity(self, graph_obj: FiberNetworkBuilder):
        r"""Returns the average connectivity of a graph G.

        The average connectivity of a graph G is the average
        of local node connectivity over all pairs of the Graph (G) nodes.

        Parameters
        ---------
        graph_obj: Graph extractor object.
        """

        nx_graph = graph_obj.nx_3d_graph
        cpu_count = get_num_cores()
        anc = 0

        try:
            filename, output_location = self.ntwk_p.get_filenames()
            g_filename = filename + "_graph.txt"
            graph_file = os.path.join(output_location, g_filename)
            nx.write_edgelist(nx_graph, graph_file, data=False)
            anc = sgt.compute_anc(graph_file, cpu_count, self.allow_mp)
        except Exception as err:
            print(err)
        return anc

    def generate_pdf_output(self, graph_obj: FiberNetworkBuilder):
        """
        Generate results as graphs and plots which should be written in a PDF file.

        :param graph_obj: Graph extractor object.

        :return: List of results.
        """

        opt_gtc = self.configs
        out_figs = []

        sel_batch = self.ntwk_p.get_selected_batch()
        sel_images = self.ntwk_p.get_selected_images(sel_batch)
        is_2d = sel_batch.is_2d
        img_3d = [img.img_2d for img in sel_images]
        img_3d = np.asarray(img_3d)

        self.update_status([90, "Generating PDF GT Output..."])

        # 1. plotting the original, processed, and binary image, as well as the histogram of pixel grayscale values
        figs = self.ntwk_p.plot_images()
        for fig in figs:
            out_figs.append(fig)

        # 2. plotting graph nodes
        fig = graph_obj.plot_2d_graph_network(image_2d_arr=img_3d, plot_nodes=True, a4_size=True)
        if fig is not None:
            out_figs.append(fig)

        # 3. plotting graph edges
        fig = graph_obj.plot_2d_graph_network(image_2d_arr=img_3d, a4_size=True)
        if fig is not None:
            out_figs.append(fig)

        # 4. displaying all the GT calculations in Table (on the entire page)
        fig, fig_wt = self.plot_gt_results(graph_obj)
        out_figs.append(fig)
        if fig_wt:
            out_figs.append(fig_wt)

        # 5. displaying histograms
        self.update_status([92, "Generating histograms..."])
        figs = self.plot_histograms(graph_obj)
        for fig in figs:
            out_figs.append(fig)

        # 6. displaying heatmaps
        if opt_gtc["display_heatmaps"]["value"] == 1:
            self.update_status([95, "Generating heatmaps..."])
            figs = self.plot_2d_heatmaps(graph_obj, image_2d=img_3d[0])
            for fig in figs:
                out_figs.append(fig)

        # 7. displaying run information
        fig = self.plot_run_configs(graph_obj)
        out_figs.append(fig)
        return out_figs

    def _update_histogram_data(self, data_dict: dict, arr_distribution: np.ndarray, hist_name: str, hist_label: str):
        val = round(np.average(arr_distribution), 5)
        self.histogram_data[hist_name] = arr_distribution
        data_dict["x"].append(hist_label)
        data_dict["y"].append(val)
        return data_dict

    def plot_gt_results(self, graph_obj: FiberNetworkBuilder):
        """
        Create a table of weighted and unweighted graph theory results.

        :param graph_obj: Graph extractor object.

        :return: Matplotlib figures of unweighted and weighted graph theory results.
        """

        opt_gte = graph_obj.configs
        data = self.output_data
        w_data = self.weighted_output_data

        fig = plt.Figure(figsize=(8.5, 11), dpi=300)
        ax = fig.add_subplot(1, 1, 1)
        ax.set_axis_off()
        ax.set_title("Unweighted GT parameters")
        col_width = [2 / 3, 1 / 3]
        tab_1 = tbl.table(ax, cellText=data.values[:, :], loc='upper center', colWidths=col_width, cellLoc='left')
        tab_1.scale(1, 1.5)

        if opt_gte["has_weights"]["value"] == 1 and w_data is not None:
            fig_wt = plt.Figure(figsize=(8.5, 11), dpi=300)
            ax = fig_wt.add_subplot(1, 1, 1)
            ax.set_axis_off()
            ax.set_title("Weighted GT parameters")
            tab_2 = tbl.table(ax, cellText=w_data.values[:, :], loc='upper center', colWidths=col_width, cellLoc='left')
            tab_2.scale(1, 1.5)
        else:
            fig_wt = None
        return fig, fig_wt

    def plot_histograms(self, graph_obj: FiberNetworkBuilder):
        """
        Create plot figures of graph theory histograms selected by the user.

        :param graph_obj: Graph extractor object.

        :return: A list of Matplotlib figures.
        """

        opt_gte = graph_obj.configs
        opt_gtc = self.configs
        figs = []

        # Degree and Closeness
        fig = plt.Figure(figsize=(8.5, 11), dpi=300)
        if opt_gtc["display_degree_histogram"]["value"] == 1:
            deg_distribution = self.histogram_data["degree_distribution"]
            bins = np.arange(0.5, max(deg_distribution) + 1.5, 1)
            deg_title = r'Degree Distribution: $\sigma$='
            ax_1 = fig.add_subplot(2, 1, 1)
            GraphAnalyzer.plot_distribution_histogram(ax_1, deg_title, deg_distribution, 'Degree', bins=bins)

        if opt_gtc["display_closeness_centrality_histogram"]["value"] == 1:
            clo_distribution = self.histogram_data["closeness_distribution"]
            cc_title = r"Closeness Centrality: $\sigma$="
            ax_2 = fig.add_subplot(2, 1, 2)
            GraphAnalyzer.plot_distribution_histogram(ax_2, cc_title, clo_distribution, 'Closeness value')
        figs.append(fig)

        # Betweenness, Clustering, Eigenvector and Ohms
        fig = plt.Figure(figsize=(8.5, 11), dpi=300)
        if opt_gtc["display_betweenness_centrality_histogram"]["value"] == 1:
            bet_distribution = self.histogram_data["betweenness_distribution"]
            bc_title = r"Betweenness Centrality: $\sigma$="
            ax_1 = fig.add_subplot(2, 2, 1)
            GraphAnalyzer.plot_distribution_histogram(ax_1, bc_title, bet_distribution, 'Betweenness value')

        if opt_gtc["compute_avg_clustering_coef"]["value"] == 1:
            cluster_coefs = self.histogram_data["clustering_coefficients"]
            clu_title = r"Clustering Coefficients: $\sigma$="
            ax_2 = fig.add_subplot(2, 2, 2)
            GraphAnalyzer.plot_distribution_histogram(ax_2, clu_title, cluster_coefs, 'Clust. Coeff.')

        if opt_gtc["display_ohms_histogram"]["value"] == 1:
            ohm_distribution = self.histogram_data["ohms_distribution"]
            oh_title = r"Ohms Centrality: $\sigma$="
            ax_3 = fig.add_subplot(2, 2, 3)
            GraphAnalyzer.plot_distribution_histogram(ax_3, oh_title, ohm_distribution, 'Ohms value')

        if opt_gtc["display_eigenvector_centrality_histogram"]["value"] == 1:
            eig_distribution = self.histogram_data["eigenvector_distribution"]
            ec_title = r"Eigenvector Centrality: $\sigma$="
            ax_4 = fig.add_subplot(2, 2, 4)
            GraphAnalyzer.plot_distribution_histogram(ax_4, ec_title, eig_distribution, 'Eigenvector value')
        figs.append(fig)

        # Currentflow

        # Percolation
        if opt_gtc["display_percolation_histogram"]["value"] == 1:
            per_distribution = self.histogram_data["percolation_distribution"]
            fig = plt.Figure(figsize=(8.5, 11), dpi=300)
            pc_title = r"Percolation Centrality: $\sigma$="
            ax_1 = fig.add_subplot(2, 2, 1)
            GraphAnalyzer.plot_distribution_histogram(ax_1, pc_title, per_distribution, 'Percolation value')
            figs.append(fig)

        # weighted histograms
        if opt_gte["has_weights"]["value"] == 1:
            wt_type = graph_obj.get_weight_type()
            weight_type = FiberNetworkBuilder.get_weight_options().get(wt_type)

            # degree, betweenness, closeness and eigenvector
            fig = plt.Figure(figsize=(8.5, 11), dpi=300)
            if opt_gtc["display_degree_histogram"]["value"] == 1:
                w_deg_distribution = self.histogram_data["weighted_degree_distribution"]
                bins = np.arange(0.5, max(w_deg_distribution) + 1.5, 1)
                w_deg_title = r"Weighted Degree: $\sigma$="
                ax_1 = fig.add_subplot(2, 2, 1)
                GraphAnalyzer.plot_distribution_histogram(ax_1, w_deg_title, w_deg_distribution, 'Degree', bins=bins)

            if opt_gtc["display_betweenness_centrality_histogram"]["value"] == 1:
                w_bet_distribution = self.histogram_data["weighted_betweenness_distribution"]
                w_bt_title = weight_type + r"-Weighted Betweenness: $\sigma$="
                ax_2 = fig.add_subplot(2, 2, 2)
                GraphAnalyzer.plot_distribution_histogram(ax_2, w_bt_title, w_bet_distribution, 'Betweenness value')

            if opt_gtc["display_closeness_centrality_histogram"]["value"] == 1:
                w_clo_distribution = self.histogram_data["weighted_closeness_distribution"]
                w_clo_title = r"Length-Weighted Closeness: $\sigma$="
                ax_3 = fig.add_subplot(2, 2, 3)
                GraphAnalyzer.plot_distribution_histogram(ax_3, w_clo_title, w_clo_distribution, 'Closeness value')

            if opt_gtc["display_eigenvector_centrality_histogram"]["value"] == 1:
                w_eig_distribution = self.histogram_data["weighted_eigenvector_distribution"]
                w_ec_title = weight_type + r"-Weighted Eigenvector Cent.: $\sigma$="
                ax_4 = fig.add_subplot(2, 2, 4)
                GraphAnalyzer.plot_distribution_histogram(ax_4, w_ec_title, w_eig_distribution, 'Eigenvector value')
            figs.append(fig)

            # percolation
            if opt_gtc["display_percolation_histogram"]["value"] == 1:
                w_per_distribution = self.histogram_data["weighted_percolation_distribution"]
                fig = plt.Figure(figsize=(8.5, 11), dpi=300)
                w_pc_title = weight_type + r"-Weighted Percolation Cent.: $\sigma$="
                ax_1 = fig.add_subplot(2, 2, 1)
                GraphAnalyzer.plot_distribution_histogram(ax_1, w_pc_title, w_per_distribution, 'Percolation value')
                figs.append(fig)

        return figs

    def plot_2d_heatmaps(self, graph_obj: FiberNetworkBuilder, image_2d: MatLike = None):
        """
        Create plot figures of graph theory heatmaps.

        :param graph_obj: GraphExtractor object.
        :param image_2d: Raw 2D images to be superimposed with heatmap.

        :return: A list of Matplotlib figures.
        """

        opt_gte = graph_obj.configs
        opt_gtc = self.configs

        sz = 30
        lw = 1.5
        figs = []
        wt_type = graph_obj.get_weight_type()
        weight_type = FiberNetworkBuilder.get_weight_options().get(wt_type)

        if opt_gtc["display_degree_histogram"]["value"] == 1:
            deg_distribution = self.histogram_data["degree_distribution"]
            fig = GraphAnalyzer.plot_distribution_heatmap(graph_obj, image_2d, deg_distribution, 'Degree Heatmap', sz, lw)
            figs.append(fig)
        if (opt_gtc["display_degree_histogram"]["value"] == 1) and (opt_gte["has_weights"]["value"] == 1):
            w_deg_distribution = self.histogram_data["weighted_degree_distribution"]
            fig = GraphAnalyzer.plot_distribution_heatmap(graph_obj, image_2d, w_deg_distribution, 'Weighted Degree Heatmap', sz, lw)
            figs.append(fig)
        if opt_gtc["compute_avg_clustering_coef"]["value"] == 1:
            cluster_coefs = self.histogram_data["clustering_coefficients"]
            fig = GraphAnalyzer.plot_distribution_heatmap(graph_obj, image_2d, cluster_coefs, 'Clustering Coefficient Heatmap', sz, lw)
            figs.append(fig)
        if opt_gtc["display_betweenness_centrality_histogram"]["value"] == 1:
            bet_distribution = self.histogram_data["betweenness_distribution"]
            fig = GraphAnalyzer.plot_distribution_heatmap(graph_obj, image_2d, bet_distribution, 'Betweenness Centrality Heatmap', sz, lw)
            figs.append(fig)
        if (opt_gtc["display_betweenness_centrality_histogram"]["value"] == 1) and (opt_gte["has_weights"]["value"] == 1):
            w_bet_distribution = self.histogram_data["weighted_betweenness_distribution"]
            fig = GraphAnalyzer.plot_distribution_heatmap(graph_obj, image_2d, w_bet_distribution,
                                    f'{weight_type}-Weighted Betweenness Centrality Heatmap', sz, lw)
            figs.append(fig)
        if opt_gtc["display_closeness_centrality_histogram"]["value"] == 1:
            clo_distribution = self.histogram_data["closeness_distribution"]
            fig = GraphAnalyzer.plot_distribution_heatmap(graph_obj, image_2d, clo_distribution, 'Closeness Centrality Heatmap', sz, lw)
            figs.append(fig)
        if (opt_gtc["display_closeness_centrality_histogram"]["value"] == 1) and (opt_gte["has_weights"]["value"] == 1):
            w_clo_distribution = self.histogram_data["weighted_closeness_distribution"]
            fig = GraphAnalyzer.plot_distribution_heatmap(graph_obj, image_2d, w_clo_distribution, 'Length-Weighted Closeness Centrality Heatmap', sz, lw)
            figs.append(fig)
        if opt_gtc["display_eigenvector_centrality_histogram"]["value"] == 1:
            eig_distribution = self.histogram_data["eigenvector_distribution"]
            fig = GraphAnalyzer.plot_distribution_heatmap(graph_obj, image_2d, eig_distribution, 'Eigenvector Centrality Heatmap', sz, lw)
            figs.append(fig)
        if (opt_gtc["display_eigenvector_centrality_histogram"]["value"] == 1) and (opt_gte["has_weights"]["value"] == 1):
            w_eig_distribution = self.histogram_data["weighted_eigenvector_distribution"]
            fig = GraphAnalyzer.plot_distribution_heatmap(graph_obj, image_2d, w_eig_distribution,
                                    f'{weight_type}-Weighted Eigenvector Centrality Heatmap', sz, lw)
            figs.append(fig)
        if opt_gtc["display_ohms_histogram"]["value"] == 1:
            ohm_distribution = self.histogram_data["ohms_distribution"]
            fig = GraphAnalyzer.plot_distribution_heatmap(graph_obj, image_2d, ohm_distribution, 'Ohms Centrality Heatmap', sz, lw)
            figs.append(fig)
        if opt_gtc["display_percolation_histogram"]["value"] == 1:
            per_distribution = self.histogram_data["percolation_distribution"]
            fig = GraphAnalyzer.plot_distribution_heatmap(graph_obj, image_2d, per_distribution, 'Percolation Centrality Heatmap', sz, lw)
            figs.append(fig)
        if (opt_gtc["display_percolation_histogram"]["value"] == 1) and (opt_gte["has_weights"]["value"] == 1):
            w_per_distribution = self.histogram_data["weighted_percolation_distribution"]
            fig = GraphAnalyzer.plot_distribution_heatmap(graph_obj, image_2d, w_per_distribution,
                                    f'{weight_type}-Weighted Percolation Centrality Heatmap', sz, lw)
            figs.append(fig)
        return figs

    def plot_run_configs(self, graph_obj: FiberNetworkBuilder):
        """
        Create a page (as a figure) that will show the user-selected parameters and options.

        :param graph_obj: GraphExtractor object.

        :return: A Matplotlib figure object.
        """

        fig = plt.Figure(figsize=(8.5, 8.5), dpi=300)
        ax = fig.add_subplot(1, 1, 1)
        ax.set_axis_off()
        ax.set_title("Run Info")

        # similar to the start of the csv file, this is just getting all the relevant settings to display in the PDF
        _, filename = os.path.split(self.ntwk_p.img_path)
        now = datetime.datetime.now()

        run_info = ""
        run_info += filename + "\n"
        run_info += now.strftime("%Y-%m-%d %H:%M:%S") + "\n----------------------------\n\n"

        # Image Configs
        sel_img_batch = self.ntwk_p.get_selected_batch()
        run_info += sel_img_batch.images[0].get_config_info()  # Get configs of first image
        run_info += "\n\n"

        # Graph Configs
        run_info += graph_obj.get_config_info()
        run_info += "\n\n"

        ax.text(0.5, 0.5, run_info, horizontalalignment='center', verticalalignment='center')
        return fig

    @staticmethod
    def compute_graph_conductance(graph_obj):
        """
        Computes graph conductance through an approach based on eigenvectors or spectral frequency.
        Implements ideas proposed in:    https://doi.org/10.1016/j.procs.2013.09.311.

        Conductance can closely be approximated via eigenvalue computation,
        a fact which has been well-known and well-used in the graph theory community.

        The Laplacian matrix of a directed graph is by definition generally non-symmetric,
        while, e.g., traditional spectral clustering is primarily developed for undirected
        graphs with symmetric adjacency and Laplacian matrices. A trivial approach to applying the
        techniques requiring symmetry is to turn the original directed graph into an
        undirected graph and build the Laplacian matrix for the latter.

        We need to remove isolated nodes (to avoid singular adjacency matrix).
        The degree of a node is the number of edges incident to that node.
        When a node has a degree of zero, it means that there are no edges
        connected to that node. In other words, the node is isolated from
        the rest of the graph.

        :param graph_obj: Graph Extractor object.

        """

        # Make a copy of the graph
        graph = graph_obj.nx_3d_graph.copy()
        weighted = graph_obj.configs["has_weights"]["value"]

        # It is important to notice our graph is (mostly) a directed graph,
        # meaning that it is: (asymmetric) with self-looping nodes

        # 1. Remove self-looping edges from the graph, they cause zero values in Degree matrix.
        # 1a. Get Adjacency matrix
        adj_mat = nx.adjacency_matrix(graph).todense()

        # 1b. Remove (self-loops) non-zero diagonal values in Adjacency matrix
        np.fill_diagonal(adj_mat, 0)

        # 1c. Create the new graph
        giant_graph = nx.from_numpy_array(adj_mat)

        # 2a. Identify isolated nodes
        isolated_nodes = list(nx.isolates(giant_graph))

        # 2b. Remove isolated nodes
        giant_graph.remove_nodes_from(isolated_nodes)

        # 3a. Check the connectivity of the graph
        # It has less than two nodes or is not connected.
        # Identify connected components
        connected_components = list(nx.connected_components(graph))
        if not connected_components:  # In case the graph is empty
            connected_components = []
        sub_graphs = [graph.subgraph(c).copy() for c in connected_components]

        giant_graph = max(sub_graphs, key=lambda g: g.number_of_nodes())

        # 4. Compute normalized-laplacian matrix
        if weighted:
            norm_laplacian_matrix = nx.normalized_laplacian_matrix(giant_graph, weight='weight').toarray()
        else:
            # norm_laplacian_matrix = compute_norm_laplacian_matrix(giant_graph)
            norm_laplacian_matrix = nx.normalized_laplacian_matrix(giant_graph).toarray()

        # 5. Compute eigenvalues
        # e_vals, _ = xp.linalg.eig(norm_laplacian_matrix)
        e_vals = sp.linalg.eigvals(norm_laplacian_matrix)

        # 6. Approximate conductance using the 2nd smallest eigenvalue
        # 6a. Compute the minimum and maximum values of graph conductance.
        sorted_vals = np.array(e_vals.real)
        sorted_vals.sort()
        # approximate conductance using the 2nd smallest eigenvalue
        try:
            # Maximum Conductance
            val_max = math.sqrt((2 * sorted_vals[1]))
        except ValueError:
            val_max = None
        # Minimum Graph Conductance
        val_min = sorted_vals[1] / 2

        return val_max, val_min

    @staticmethod
    def plot_distribution_heatmap(graph_obj: FiberNetworkBuilder, image: MatLike, distribution: list, title: str, size: float, line_width: float):
        """
        Create a heatmap from a distribution.

        :param graph_obj: GraphExtractor object.
        :param image: Image to plot.
        :param distribution: Dataset to be plotted.
        :param title: Title of the plot figure.
        :param size: Size of the scatter items.
        :param line_width: Size of the plot line-width.
        :return: Histogram plot figure.
        """
        nx_graph = graph_obj.nx_3d_graph
        font_1 = {'fontsize': 9}

        fig = plt.Figure(figsize=(8.5, 8.5), dpi=400)
        ax = fig.add_subplot(1, 1, 1)
        ax.set_title(title, fontdict=font_1)

        FiberNetworkBuilder.plot_graph_edges(ax, image, nx_graph, line_width=line_width)
        c_set = FiberNetworkBuilder.plot_graph_nodes(ax, nx_graph, marker_size=size, distribution_data=distribution)

        fig.colorbar(c_set, ax=ax, orientation='vertical', label='Value')
        return fig

    @staticmethod
    def plot_distribution_histogram(ax: plt.axes, title: str, distribution: list, x_label: str, bins: np.ndarray = None,
                                    y_label: str = 'Counts'):
        """
        Create a histogram from a distribution dataset.

        :param ax: Plot axis.
        :param title: Title text.
        :param distribution: Dataset to be plotted.
        :param x_label: X-label title text.
        :param bins: Bin dataset.
        :param y_label: Y-label title text.
        :return:
        """
        font_1 = {'fontsize': 9}
        if bins is None:
            bins = np.linspace(min(distribution), max(distribution), 50)
        try:
            std_val = str(round(stdev(distribution), 3))
        except StatisticsError:
            std_val = "N/A"
        hist_title = title + std_val
        ax.set_title(hist_title, fontdict=font_1)
        ax.set(xlabel=x_label, ylabel=y_label)
        ax.hist(distribution, bins=bins)
