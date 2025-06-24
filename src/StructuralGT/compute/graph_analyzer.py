# SPDX-License-Identifier: GNU GPL v3

"""
Compute graph theory metrics
"""

import os
import math
import time
import datetime
import itertools
import logging
import multiprocessing
import numpy as np
import scipy as sp
import pandas as pd
import networkx as nx
import matplotlib.table as tbl
import matplotlib.pyplot as plt
from cv2.typing import MatLike
from collections import defaultdict
from statistics import stdev, StatisticsError
from matplotlib.backends.backend_pdf import PdfPages

from networkx.algorithms.centrality import betweenness_centrality, closeness_centrality, eigenvector_centrality
from networkx.algorithms import average_node_connectivity, global_efficiency, clustering
from networkx.algorithms import degree_assortativity_coefficient
from networkx.algorithms.flow import maximum_flow
from networkx.algorithms.distance_measures import diameter, periphery
from networkx.algorithms.wiener import wiener_index

from .c_lang import sgt_c_module as sgt
from ..utils.progress_update import ProgressUpdate
from ..networks.fiber_network import FiberNetworkBuilder
from ..imaging.image_processor import ImageProcessor
from ..utils.config_loader import load_gtc_configs
from ..utils.sgt_utils import get_num_cores, AbortException, write_txt_file

logger = logging.getLogger("SGT App")

# WE ARE USING CPU BECAUSE CuPy generates some errors - yet to be resolved.
COMPUTING_DEVICE = "CPU"
"""
try:
    import sys
    import cupy as cp

    # Check for GPU
    test = cp.cuda.Device(0).compute_capability
    # Check for CUDA_PATH in environment variables
    cuda_path = os.getenv("CUDA_PATH")
    print(cuda_path)
    if cuda_path:
        xp = np  # Use CuPy for GPU
        COMPUTING_DEVICE = "GPU"
        logging.info("Using GPU with CuPy!", extra={'user': 'SGT Logs'})
    else:
        logging.info(
            "Please add CUDA_PATH to System environment variables OR install 'NVIDIA GPU Computing Toolkit'\nvia: https://developer.nvidia.com/cuda-downloads",
            extra={'user': 'SGT Logs'})
        raise ImportError("Please add CUDA_PATH to System environment variables.")
except (ImportError, NameError, AttributeError):
    xp = np  # Fallback to NumPy for CPU
    logging.info("Using CPU with NumPy!", extra={'user': 'SGT Logs'})
except cp.cuda.runtime.CUDARuntimeError:
    xp = np  # Fallback to NumPy for CPU
    logging.info("Using CPU with NumPy!", extra={'user': 'SGT Logs'})
"""


class GraphAnalyzer(ProgressUpdate):
    """
    A class that computes all the user-selected graph theory metrics and writes the results in a PDF file.

    Args:
        :param imp: Image Processor object.
        allow_multiprocessing: a decision to allow multiprocessing computing.
    """

    def __init__(self, imp: ImageProcessor, allow_multiprocessing: bool = True):
        """
        A class that computes all the user-selected graph theory metrics and writes the results in a PDF file.

        :param imp: Image Processor object.
        :param allow_multiprocessing: Allows multiprocessing computing.

        >>> i_path = "path/to/image"
        >>> o_dir = ""
        >>>
        >>> ntwk_obj = ImageProcessor(i_path, o_dir)
        >>> metrics_obj = GraphAnalyzer(ntwk_obj)
        >>> metrics_obj.run_analyzer()
        """
        super(GraphAnalyzer, self).__init__()
        self.configs: dict = load_gtc_configs(imp.config_file)  # graph theory computation parameters and options.
        self.props: list = []
        self.allow_mp: bool = allow_multiprocessing
        self.ntwk_p: ImageProcessor = imp
        self.plot_figures: list | None = None
        self.scaling_data = None
        self.output_df: pd.DataFrame | None = None
        self.weighted_output_df: pd.DataFrame | None = None
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
        if graph_obj.nx_graph is None:
            self.ntwk_p.add_listener(self.track_img_progress)
            self.ntwk_p.apply_img_filters()  # Apply image filters
            self.ntwk_p.build_graph_network()  # Extract graph from binary image
            self.ntwk_p.remove_listener(self.track_img_progress)
            self.abort = self.ntwk_p.abort
            self.update_status([100, "Graph successfully extracted!"]) if not self.abort else None
            sel_batch = self.ntwk_p.get_selected_batch()
            graph_obj = sel_batch.graph_obj

        if self.abort:
            return

        # 3a. Compute Unweighted GT parameters
        self.output_df = self.compute_gt_metrics(graph_obj.nx_graph)

        # 3b. Compute Scaling Scatter Plots
        if self.configs["compute_scaling_behavior"]["value"] == 1:
            self.scaling_data = self.compute_scaling_data(full_img_df=self.output_df.copy())

        if self.abort:
            self.update_status([-1, "Problem encountered while computing un-weighted GT parameters."])
            return

        # 4. Compute Weighted GT parameters (skip if MultiGraph)
        self.weighted_output_df = self.compute_weighted_gt_metrics(graph_obj)

        if self.abort:
            self.update_status([-1, "Problem encountered while computing weighted GT parameters."])
            return

        # 5. Save GT compute metrics into props
        self.get_compute_props()

        # 6. Generate results in PDF
        self.plot_figures = self.generate_pdf_output(graph_obj)

    def compute_gt_metrics(self, graph: nx.Graph = None, save_histogram: bool = True):
        """
        Compute unweighted graph theory metrics.

        :param graph: NetworkX graph object.
        :param save_histogram: Whether to save the histogram data.

        :return: A Pandas DataFrame containing the unweighted graph theory metrics.
        """

        if graph is None:
            return None

        self.update_status([1, "Performing un-weighted analysis..."])

        opt_gtc = self.configs
        data_dict = {"parameter": [], "value": []}

        node_count = int(nx.number_of_nodes(graph))
        edge_count = int(nx.number_of_edges(graph))

        data_dict["parameter"].append("Number of nodes")
        data_dict["value"].append(node_count)

        data_dict["parameter"].append("Number of edges")
        data_dict["value"].append(edge_count)

        """
        # length of edges
        length_arr = np.array(list(nx.get_edge_attributes(graph, 'length').values()))
        data_dict["parameter"].append('Average length (nm)')
        data_dict["value"].append(round(np.average(length_arr), 3))
        data_dict["parameter"].append('Median length (nm)')
        data_dict["value"].append(round(np.median(length_arr), 3))

        # width of edges
        width_arr = np.array(list(nx.get_edge_attributes(graph, 'width').values()))
        data_dict["parameter"].append('Average width (nm)')
        data_dict["value"].append(round(np.average(width_arr), 3))
        data_dict["parameter"].append('Median width (nm)')
        data_dict["value"].append(round(np.median(width_arr), 3))
        """

        # angle of edges (inbound and outbound)
        angle_arr = np.array(list(nx.get_edge_attributes(graph, 'angle').values()))
        data_dict["parameter"].append('Average edge angle (degrees)')
        data_dict["value"].append(round(np.average(angle_arr), 3))
        data_dict["parameter"].append('Median edge angle (degrees)')
        data_dict["value"].append(round(np.median(angle_arr), 3))

        if graph.number_of_nodes() <= 0:
            self.update_status([-1, "Problem with graph (change filter and graph options)."])
            return None

        # creating degree histogram
        if opt_gtc["display_degree_histogram"]["value"] == 1:
            self.update_status([5, "Computing graph degree..."])
            deg_distribution_1 = dict(nx.degree(graph))
            deg_distribution = np.array(list(deg_distribution_1.values()), dtype=float)
            if save_histogram:
                self.histogram_data["degree_distribution"] = deg_distribution
            data_dict["parameter"].append("Average degree")
            data_dict["value"].append(round(np.average(deg_distribution), 5))

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
                dia = np.nan
            data_dict["parameter"].append("Network diameter")
            data_dict["value"].append(dia)

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
                    avg_node_con = self.igraph_average_node_connectivity(graph)
                else:
                    # Use NetworkX Lib in Python
                    self.update_status([15, "Using NetworkX library..."])
                    if self.allow_mp:  # Multi-processing
                        avg_node_con = self.average_node_connectivity(graph)
                    else:
                        avg_node_con = average_node_connectivity(graph)
                avg_node_con = round(avg_node_con, 5)
            else:
                avg_node_con = np.nan
            data_dict["parameter"].append("Average node connectivity")
            data_dict["value"].append(avg_node_con)

        # calculating graph density
        if opt_gtc["compute_graph_density"]["value"] == 1:
            self.update_status([20, "Computing graph density..."])
            g_density = nx.density(graph)
            g_density = round(g_density, 5)
            data_dict["parameter"].append("Graph density")
            data_dict["value"].append(g_density)

        # calculating global efficiency
        if opt_gtc["compute_global_efficiency"]["value"] == 1:
            if self.abort:
                self.update_status([-1, "Task aborted."])
                return None
            self.update_status([25, "Computing global efficiency..."])
            g_eff = global_efficiency(graph)
            g_eff = round(g_eff, 5)
            data_dict["parameter"].append("Global efficiency")
            data_dict["value"].append(g_eff)

        if opt_gtc["compute_wiener_index"]["value"] == 1:
            self.update_status([30, "Computing wiener index..."])
            # settings.update_label("Calculating w_index...")
            w_index = wiener_index(graph)
            w_index = round(w_index, 1)
            data_dict["parameter"].append("Wiener Index")
            data_dict["value"].append(w_index)

        # calculating assortativity coefficient
        if opt_gtc["compute_assortativity_coef"]["value"] == 1:
            self.update_status([35, "Computing assortativity coefficient..."])
            a_coef = degree_assortativity_coefficient(graph)
            a_coef = round(a_coef, 5)
            data_dict["parameter"].append("Assortativity coefficient")
            data_dict["value"].append(a_coef)

        # calculating clustering coefficients
        if opt_gtc["compute_avg_clustering_coef"]["value"] == 1:
            self.update_status([40, "Computing clustering coefficients..."])
            coefficients_1 = clustering(graph)
            cl_coefficients = np.array(list(coefficients_1.values()), dtype=float)
            if save_histogram:
                self.histogram_data["clustering_coefficients"] = cl_coefficients
            data_dict["parameter"].append("Average clustering coefficient")
            data_dict["value"].append(round(np.average(cl_coefficients), 5))

        # calculating betweenness centrality histogram
        if opt_gtc["display_betweenness_centrality_histogram"]["value"] == 1:
            self.update_status([45, "Computing betweenness centrality..."])
            b_distribution_1 = betweenness_centrality(graph)
            b_distribution = np.array(list(b_distribution_1.values()), dtype=float)
            if save_histogram:
                self.histogram_data["betweenness_distribution"] = b_distribution
            data_dict["parameter"].append("Average betweenness centrality")
            data_dict["value"].append(round(np.average(b_distribution), 5))

        # calculating eigenvector centrality
        if opt_gtc["display_eigenvector_centrality_histogram"]["value"] == 1:
            self.update_status([50, "Computing eigenvector centrality..."])
            try:
                e_vecs_1 = eigenvector_centrality(graph, max_iter=100)
            except nx.exception.PowerIterationFailedConvergence:
                e_vecs_1 = eigenvector_centrality(graph, max_iter=10000)
            e_vecs = np.array(list(e_vecs_1.values()), dtype=float)
            if save_histogram:
                self.histogram_data["eigenvector_distribution"] = e_vecs
            data_dict["parameter"].append("Average eigenvector centrality")
            data_dict["value"].append(round(np.average(e_vecs), 5))

        # calculating closeness centrality
        if opt_gtc["display_closeness_centrality_histogram"]["value"] == 1:
            self.update_status([55, "Computing closeness centrality..."])
            close_distribution_1 = closeness_centrality(graph)
            close_distribution = np.array(list(close_distribution_1.values()), dtype=float)
            if save_histogram:
                self.histogram_data["closeness_distribution"] = close_distribution
            data_dict["parameter"].append("Average closeness centrality")
            data_dict["value"].append(round(np.average(close_distribution), 5))

        # calculating Ohms centrality
        if opt_gtc["display_ohms_histogram"]["value"] == 1:
            self.update_status([60, "Computing Ohms centrality..."])
            o_distribution_1, res = self.compute_ohms_centrality(graph)
            o_distribution = np.array(list(o_distribution_1.values()), dtype=float)
            if save_histogram:
                self.histogram_data["ohms_distribution"] = o_distribution
            data_dict["parameter"].append("Average Ohms centrality")
            data_dict["value"].append(round(np.average(o_distribution), 5))
            data_dict["parameter"].append("Ohms centrality -- avg. area " + r"($m^2$)")
            data_dict["value"].append(res['avg area'])
            data_dict["parameter"].append("Ohms centrality -- avg. length (m)")
            data_dict["value"].append(res['avg length'])
            data_dict["parameter"].append("Ohms centrality -- avg. width (m)")
            data_dict["value"].append(res['avg width'])
            data_dict["parameter"].append("Ohms centrality -- g shape coeff.")
            data_dict["value"].append(res['g shape'])
            data_dict["parameter"].append("Ohms centrality -- conductivity (S/m)")
            data_dict["value"].append(res['conductivity'])

        return pd.DataFrame(data_dict)

    def compute_weighted_gt_metrics(self, graph_obj: FiberNetworkBuilder = None, save_histogram: bool = True):
        """
        Compute weighted graph theory metrics.

        :param graph_obj: GraphExtractor object.
        :param save_histogram: Whether to save histogram data.

        :return: A Pandas DataFrame containing the weighted graph theory metrics.
        """
        if graph_obj is None:
            return None

        if not graph_obj.configs["has_weights"]["value"]:
            return None

        self.update_status([70, "Performing weighted analysis..."])

        graph = graph_obj.nx_graph
        opt_gtc = self.configs
        wt_type = graph_obj.get_weight_type()
        weight_type = FiberNetworkBuilder.get_weight_options().get(wt_type)
        data_dict = {"parameter": [], "value": []}

        if graph.number_of_nodes() <= 0:
            self.update_status([-1, "Problem with graph (change filter and graph options)."])
            return None

        if opt_gtc["display_degree_histogram"]["value"] == 1:
            self.update_status([72, "Compute weighted graph degree..."])
            deg_distribution_1 = dict(nx.degree(graph, weight='weight'))
            deg_distribution = np.array(list(deg_distribution_1.values()), dtype=float)
            if save_histogram:
                self.histogram_data["weighted_degree_distribution"] = deg_distribution
            data_dict["parameter"].append(f"{weight_type}-weighted average degree")
            data_dict["value"].append(round(np.average(deg_distribution), 5))

        if opt_gtc["compute_wiener_index"]["value"] == 1:
            self.update_status([74, "Compute weighted wiener index..."])
            w_index = wiener_index(graph, weight='length')
            w_index = round(w_index, 1)
            data_dict["parameter"].append("Length-weighted Wiener Index")
            data_dict["value"].append(w_index)

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
                max_flow = np.nan
            data_dict["parameter"].append("Max flow between periphery")
            data_dict["value"].append(max_flow)

        if opt_gtc["compute_assortativity_coef"]["value"] == 1:
            self.update_status([78, "Compute weighted assortativity..."])
            a_coef = degree_assortativity_coefficient(graph, weight='width')
            a_coef = round(a_coef, 5)
            data_dict["parameter"].append("Width-weighted assortativity coefficient")
            data_dict["value"].append(a_coef)

        if opt_gtc["display_betweenness_centrality_histogram"]["value"] == 1:
            self.update_status([80, "Compute weighted betweenness centrality..."])
            b_distribution_1 = betweenness_centrality(graph, weight='weight')
            b_distribution = np.array(list(b_distribution_1.values()), dtype=float)
            if save_histogram:
                self.histogram_data["weighted_betweenness_distribution"] = b_distribution
            data_dict["parameter"].append(f"{weight_type}-weighted betweenness centrality")
            data_dict["value"].append(round(np.average(b_distribution), 5))

        if opt_gtc["display_closeness_centrality_histogram"]["value"] == 1:
            self.update_status([82, "Compute weighted closeness centrality..."])
            close_distribution_1 = closeness_centrality(graph, distance='length')
            close_distribution = np.array(list(close_distribution_1.values()), dtype=float)
            if save_histogram:
                self.histogram_data["weighted_closeness_distribution"] = close_distribution
            data_dict["parameter"].append(f"Length-weighted average closeness centrality")
            data_dict["value"].append(round(np.average(close_distribution), 5))

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
            if save_histogram:
                self.histogram_data["weighted_eigenvector_distribution"] = e_vecs
            data_dict["parameter"].append(f"{weight_type}-weighted average eigenvector centrality")
            data_dict["value"].append(round(np.average(e_vecs), 5))

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
            data_dict["parameter"].append(f"Average edge cross-sectional area (nm\u00b2)")
            data_dict["value"].append(ae_val)

        return pd.DataFrame(data_dict)

    def compute_scaling_data(self, full_img_df: pd.DataFrame = None):
        """"""
        self.update_status([0, "Computing scaling behaviour..."])
        self.ntwk_p.add_listener(self.track_img_progress)
        # Get from configs
        graph_groups = self.ntwk_p.build_graph_from_patches(num_square_filters=10, patch_count_per_filter=10)
        self.ntwk_p.remove_listener(self.track_img_progress)

        sorted_plt_data = defaultdict(lambda: defaultdict(list))
        num_patches = 1
        for (h, w), nx_graphs in graph_groups.items():
            num_patches = len(nx_graphs)
            for nx_graph in nx_graphs:
                temp_df = self.compute_gt_metrics(nx_graph, save_histogram=False)
                if temp_df is None:
                    # Skip the problematic graph
                    continue

                for _, row in temp_df.iterrows():
                    x_param = row["parameter"]
                    y_value = row["value"]
                    if ' edge angle' in x_param:  # Skip this
                        continue
                    sorted_plt_data[x_param][h].append(y_value)

        # Include the computed GT metrics of the entire image
        if full_img_df is not None:
            # Get full image dimensions
            sel_batch = self.ntwk_p.get_selected_batch()
            h, w = sel_batch.images[0].img_bin.shape
            for _ in range(num_patches):
                for _, row in full_img_df.iterrows():
                    x_param = row["parameter"]
                    y_value = row["value"]
                    # print(f"{x_param}-{h}: {y_value}")
                    sorted_plt_data[x_param][h].append(y_value)
        return sorted_plt_data

    def compute_ohms_centrality(self, nx_graph: nx.Graph):
        r"""
        Computes Ohms centrality value for each node based on actual pixel width and length of edges in meters.

        :param nx_graph: NetworkX graph object.

        Returns: Ohms centrality distribution
        """
        ohms_dict = {}
        lst_area = []
        lst_len = []
        lst_width = []

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
        med_area = np.median(np.array(lst_area, dtype=float))
        avg_len = np.average(np.array(lst_len, dtype=float))
        med_len = np.median(np.array(lst_len, dtype=float))
        avg_width = np.average(np.array(lst_width, dtype=float))
        med_width = np.median(np.array(lst_width, dtype=float))
        res = {
            'avg area': avg_area, 'med area': med_area,
            'avg length': avg_len, 'med length': med_len,
            'avg width': avg_width, 'med width': med_width,
            'g shape': g_shape, 'conductivity': round((1 / rho_dim), 2)}

        return ohms_dict, res

    def average_node_connectivity(self, nx_graph: nx.Graph, flow_func=None):
        r"""Returns the average connectivity of a graph G.

        The average connectivity `\bar{\kappa}` of a graph G is the average
        of local node connectivity over all pairs of the nx_graph nodes.

        https://networkx.org/documentation/stable/_modules/networkx/algorithms/connectivity/connectivity.html#average_node_connectivity

        Parameters
        ----------
        :param nx_graph: NetworkX graph object.
        :param flow_func : Function
            A function for computing the maximum flow between a pair of nodes.
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

    def igraph_average_node_connectivity(self, nx_graph: nx.Graph):
        r"""Returns the average connectivity of a graph G.

        The average connectivity of a graph G is the average
        of local node connectivity over all pairs of the Graph (G) nodes.

        Parameters
        ---------
        :param nx_graph: NetworkX graph object.
        """

        cpu_count = get_num_cores()
        num_threads = cpu_count if nx.number_of_nodes(nx_graph) < 2000 else cpu_count * 2
        anc = 0

        try:
            filename, output_location = self.ntwk_p.get_filenames()
            g_filename = filename + "_graph.txt"
            graph_file = os.path.join(output_location, g_filename)
            nx.write_edgelist(nx_graph, graph_file, data=False)
            anc = sgt.compute_anc(graph_file, num_threads, self.allow_mp)
        except Exception as err:
            logging.exception("Computing ANC Error: %s", err, extra={'user': 'SGT Logs'})
        return anc

    def compute_graph_conductance(self, graph_obj):
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
        self.update_status([101, "Computing graph conductance..."])
        # Make a copy of the graph
        graph = graph_obj.nx_graph.copy()
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
            val_max = np.nan
        # Minimum Graph Conductance
        val_min = sorted_vals[1] / 2

        return val_max, val_min

    def get_compute_props(self):
        """
        A method that retrieves graph theory computed parameters and stores them in a list-array.

        Returns: list of computed GT params.

        """
        self.props = []
        # 1. Unweighted parameters
        if self.output_df is None:
            return
        param_df = self.output_df.copy()
        self.props.append(['UN-WEIGHTED', 'PARAMETERS'])
        for _, row in param_df.iterrows():
            x_param = row["parameter"]
            y_value = row["value"]
            self.props.append([x_param, y_value])

        # 2. Weighted parameters
        if self.weighted_output_df is None:
            return
        param_df = self.weighted_output_df.copy()
        self.props.append(['WEIGHTED', 'PARAMETERS'])
        for _, row in param_df.iterrows():
            x_param = row["parameter"]
            y_value = row["value"]
            self.props.append([x_param, y_value])

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

        # 4a. displaying all the GT calculations in Table (on the entire page)
        fig, fig_wt = self.plot_gt_results(graph_obj)
        out_figs.append(fig)
        if fig_wt:
            out_figs.append(fig_wt)

        # 4b. display scaling GT results in a Table
        figs = GraphAnalyzer.plot_scaling_behavior(self.scaling_data)
        for fig in figs:
            out_figs.append(fig)

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

    def plot_gt_results(self, graph_obj: FiberNetworkBuilder):
        """
        Create a table of weighted and unweighted graph theory results.

        :param graph_obj: Graph extractor object.

        :return: Matplotlib figures of unweighted and weighted graph theory results.
        """

        opt_gte = graph_obj.configs
        data = self.output_df
        w_data = self.weighted_output_df

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

        def plot_distribution_histogram(ax: plt.axes, title: str, distribution: list, x_label: str,
                                        plt_bins: np.ndarray = None, y_label: str = 'Counts'):
            """
            Create a histogram from a distribution dataset.

            :param ax: Plot axis.
            :param title: Title text.
            :param distribution: Dataset to be plotted.
            :param x_label: X-label title text.
            :param plt_bins: Bin dataset.
            :param y_label: Y-label title text.
            :return:
            """
            font_1 = {'fontsize': 9}
            if plt_bins is None:
                plt_bins = np.linspace(min(distribution), max(distribution), 50)
            try:
                std_val = str(round(stdev(distribution), 3))
            except StatisticsError:
                std_val = "N/A"
            hist_title = title + std_val
            ax.set_title(hist_title, fontdict=font_1)
            ax.set(xlabel=x_label, ylabel=y_label)
            ax.hist(distribution, bins=plt_bins)

        # Degree and Closeness
        fig = plt.Figure(figsize=(8.5, 11), dpi=300)
        if opt_gtc["display_degree_histogram"]["value"] == 1:
            deg_distribution = self.histogram_data["degree_distribution"]
            bins = np.arange(0.5, max(deg_distribution) + 1.5, 1)
            deg_title = r'Degree Distribution: $\sigma$='
            ax_1 = fig.add_subplot(2, 1, 1)
            plot_distribution_histogram(ax_1, deg_title, deg_distribution, 'Degree', plt_bins=bins)

        if opt_gtc["display_closeness_centrality_histogram"]["value"] == 1:
            clo_distribution = self.histogram_data["closeness_distribution"]
            cc_title = r"Closeness Centrality: $\sigma$="
            ax_2 = fig.add_subplot(2, 1, 2)
            plot_distribution_histogram(ax_2, cc_title, clo_distribution, 'Closeness value')
        figs.append(fig)

        # Betweenness, Clustering, Eigenvector and Ohms
        fig = plt.Figure(figsize=(8.5, 11), dpi=300)
        if opt_gtc["display_betweenness_centrality_histogram"]["value"] == 1:
            bet_distribution = self.histogram_data["betweenness_distribution"]
            bc_title = r"Betweenness Centrality: $\sigma$="
            ax_1 = fig.add_subplot(2, 2, 1)
            plot_distribution_histogram(ax_1, bc_title, bet_distribution, 'Betweenness value')

        if opt_gtc["compute_avg_clustering_coef"]["value"] == 1:
            cluster_coefs = self.histogram_data["clustering_coefficients"]
            clu_title = r"Clustering Coefficients: $\sigma$="
            ax_2 = fig.add_subplot(2, 2, 2)
            plot_distribution_histogram(ax_2, clu_title, cluster_coefs, 'Clust. Coeff.')

        if opt_gtc["display_ohms_histogram"]["value"] == 1:
            ohm_distribution = self.histogram_data["ohms_distribution"]
            oh_title = r"Ohms Centrality: $\sigma$="
            ax_3 = fig.add_subplot(2, 2, 3)
            plot_distribution_histogram(ax_3, oh_title, ohm_distribution, 'Ohms value')

        if opt_gtc["display_eigenvector_centrality_histogram"]["value"] == 1:
            eig_distribution = self.histogram_data["eigenvector_distribution"]
            ec_title = r"Eigenvector Centrality: $\sigma$="
            ax_4 = fig.add_subplot(2, 2, 4)
            plot_distribution_histogram(ax_4, ec_title, eig_distribution, 'Eigenvector value')
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
                plot_distribution_histogram(ax_1, w_deg_title, w_deg_distribution, 'Degree', plt_bins=bins)

            if opt_gtc["display_betweenness_centrality_histogram"]["value"] == 1:
                w_bet_distribution = self.histogram_data["weighted_betweenness_distribution"]
                w_bt_title = weight_type + r"-Weighted Betweenness: $\sigma$="
                ax_2 = fig.add_subplot(2, 2, 2)
                plot_distribution_histogram(ax_2, w_bt_title, w_bet_distribution, 'Betweenness value')

            if opt_gtc["display_closeness_centrality_histogram"]["value"] == 1:
                w_clo_distribution = self.histogram_data["weighted_closeness_distribution"]
                w_clo_title = r"Length-Weighted Closeness: $\sigma$="
                ax_3 = fig.add_subplot(2, 2, 3)
                plot_distribution_histogram(ax_3, w_clo_title, w_clo_distribution, 'Closeness value')

            if opt_gtc["display_eigenvector_centrality_histogram"]["value"] == 1:
                w_eig_distribution = self.histogram_data["weighted_eigenvector_distribution"]
                w_ec_title = weight_type + r"-Weighted Eigenvector Cent.: $\sigma$="
                ax_4 = fig.add_subplot(2, 2, 4)
                plot_distribution_histogram(ax_4, w_ec_title, w_eig_distribution, 'Eigenvector value')
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

        def plot_distribution_heatmap( distribution: list, title: str, size: float, line_width: float):
            """
            Create a heatmap from a distribution.

            :param distribution: Dataset to be plotted.
            :param title: Title of the plot figure.
            :param size: Size of the scatter items.
            :param line_width: Size of the plot line-width.
            :return: Histogram plot figure.
            """
            nx_graph = graph_obj.nx_graph
            is_2d = graph_obj.skel_obj.is_2d
            font_1 = {'fontsize': 9}

            plt_fig = plt.Figure(figsize=(8.5, 8.5), dpi=400)
            ax = plt_fig.add_subplot(1, 1, 1)
            ax.set_title(title, fontdict=font_1)

            FiberNetworkBuilder.plot_graph_edges(ax, image_2d, nx_graph, is_graph_2d=is_2d, line_width=line_width)
            c_set = FiberNetworkBuilder.plot_graph_nodes(ax, nx_graph, is_graph_2d=is_2d, marker_size=size,
                                                         distribution_data=distribution)

            plt_fig.colorbar(c_set, ax=ax, orientation='vertical', label='Value')
            return plt_fig

        if opt_gtc["display_degree_histogram"]["value"] == 1:
            deg_distribution = self.histogram_data["degree_distribution"]
            fig = plot_distribution_heatmap(deg_distribution, 'Degree Heatmap', sz, lw)
            figs.append(fig)
        if (opt_gtc["display_degree_histogram"]["value"] == 1) and (opt_gte["has_weights"]["value"] == 1):
            w_deg_distribution = self.histogram_data["weighted_degree_distribution"]
            plt_title = 'Weighted Degree Heatmap'
            fig = plot_distribution_heatmap(w_deg_distribution, plt_title, sz, lw)
            figs.append(fig)
        if opt_gtc["compute_avg_clustering_coef"]["value"] == 1:
            cluster_coefs = self.histogram_data["clustering_coefficients"]
            plt_title = 'Clustering Coefficient Heatmap'
            fig = plot_distribution_heatmap(cluster_coefs, plt_title, sz, lw)
            figs.append(fig)
        if opt_gtc["display_betweenness_centrality_histogram"]["value"] == 1:
            bet_distribution = self.histogram_data["betweenness_distribution"]
            plt_title = 'Betweenness Centrality Heatmap'
            fig = plot_distribution_heatmap(bet_distribution, plt_title, sz, lw)
            figs.append(fig)
        if (opt_gtc["display_betweenness_centrality_histogram"]["value"] == 1) and (
                opt_gte["has_weights"]["value"] == 1):
            w_bet_distribution = self.histogram_data["weighted_betweenness_distribution"]
            plt_title = f'{weight_type}-Weighted Betweenness Centrality Heatmap'
            fig = plot_distribution_heatmap(w_bet_distribution, plt_title, sz, lw)
            figs.append(fig)
        if opt_gtc["display_closeness_centrality_histogram"]["value"] == 1:
            clo_distribution = self.histogram_data["closeness_distribution"]
            plt_title = 'Closeness Centrality Heatmap'
            fig = plot_distribution_heatmap(clo_distribution, plt_title, sz, lw)
            figs.append(fig)
        if (opt_gtc["display_closeness_centrality_histogram"]["value"] == 1) and (opt_gte["has_weights"]["value"] == 1):
            w_clo_distribution = self.histogram_data["weighted_closeness_distribution"]
            plt_title = 'Length-Weighted Closeness Centrality Heatmap'
            fig = plot_distribution_heatmap(w_clo_distribution, plt_title, sz, lw)
            figs.append(fig)
        if opt_gtc["display_eigenvector_centrality_histogram"]["value"] == 1:
            eig_distribution = self.histogram_data["eigenvector_distribution"]
            plt_title = 'Eigenvector Centrality Heatmap'
            fig = plot_distribution_heatmap(eig_distribution, plt_title, sz, lw)
            figs.append(fig)
        if (opt_gtc["display_eigenvector_centrality_histogram"]["value"] == 1) and (
                opt_gte["has_weights"]["value"] == 1):
            w_eig_distribution = self.histogram_data["weighted_eigenvector_distribution"]
            plt_title = f'{weight_type}-Weighted Eigenvector Centrality Heatmap'
            fig = plot_distribution_heatmap(w_eig_distribution, plt_title, sz, lw)
            figs.append(fig)
        if opt_gtc["display_ohms_histogram"]["value"] == 1:
            ohm_distribution = self.histogram_data["ohms_distribution"]
            plt_title = 'Ohms Centrality Heatmap'
            fig = plot_distribution_heatmap(ohm_distribution, plt_title, sz, lw)
            figs.append(fig)
        print("Successfully plotted heatmaps")
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
    def plot_scaling_behavior(scaling_data: defaultdict = None):
        """"""

        # Define our 'best-fit' model
        def power_law_model(x, a, k):
            """
            A best-fit model that follows the power law distribution: y = a * x^(-k),
            where a and k are fitting parameters.

            Args:
                x (np.array): Array of x values
                a (float): fitting parameter
                k (float): fitting parameter
            """
            return a * x ** (-k)

        def truncated_power_law_model(x, a, k, c):
            """
            A best-fit model that follows the truncated power law distribution: y = a * x^(-k) * exp(-c * x),
            where a, c and k are fitting parameters.

            https://en.wikipedia.org/wiki/Power_law#Power_law_with_exponential_cutoff

            Args:
                x (np.array): Array of x values
                a (float): fitting parameter
                k (float): fitting parameter
                c (float): cut-off fitting parameter
            """
            return a * (x ** (-k)) * np.exp(-c * x)

        def lognormal_model(x, mu, sigma, a):
            """
            Log-normal model (Y depends on X, X is log-normal).

            Args:
                x (np.array): Array of x values
                mu (float): fitting parameter
                sigma (float): fitting parameter
                a (float): fitting parameter

            Returns:

            """
            return a * (1 / (x * sigma * np.sqrt(2 * np.pi))) * np.exp(-((np.log(x) - mu) ** 2) / (2 * sigma ** 2))

        def plot_axis(subplot_num, plt_type="", plot_err=True):
            """"""
            subplot_num += 1
            axis = fig.add_subplot(2, 2, subplot_num)
            if plot_err:
                axis.errorbar(x_avg, y_avg, xerr=x_err, yerr=y_err, label='Data', color='b', capsize=4, marker='s',
                        markersize=4, linewidth=1, linestyle='-')
            axis.set_title(f"{plt_type}\nNodes vs {y_title}", fontsize=10)
            axis.set(xlabel='No. of Nodes', ylabel=f'{param_name}')
            # axis.legend()
            return axis, subplot_num

        # Initialize plot figures
        figs = []
        if scaling_data is None:
            return figs

        # Plot scaling behavior
        i = 0
        x_label = None
        x_values, x_avg, x_err = np.nan, np.nan, np.nan
        fig = plt.Figure(figsize=(8.5, 11), dpi=300)
        for param_name, plt_dict in scaling_data.items():
            # Retrieve plot data
            box_labels = sorted(plt_dict.keys())  # Optional: sort heights
            y_lst = [plt_dict[h] for h in box_labels]  # shape: (n_samples, n_boxes)

            # Pad with NaN
            max_len = max(len(row) for row in y_lst)
            padded_lst = [row + [np.nan] * (max_len - len(row)) for row in y_lst]

            # Convert to a Numpy array
            y_values = np.array(padded_lst).T
            y_avg = np.nanmean(y_values, axis=0)
            y_err = np.nanstd(y_values, axis=0, ddof=1) / np.sqrt(y_values.shape[0])
            if np.any(np.isnan(y_avg)):
                # print(f"{param_name} has NaN values: {y_avg}")
                continue

            # Plot of the nodes counts against others
            if x_label is None:
                x_label = param_name
                # x_values = y_values
                x_avg = y_avg
                x_err = y_err
            else:
                # 1. Transform to log-log scale
                log_x = np.log10(x_avg)
                log_y = np.log10(y_avg)
                x_fit = np.linspace(min(x_avg), max(x_avg), 100)
                y_title = param_name.split('(')[0] if '(' in param_name else param_name

                # 2a. Perform linear regression in log-log scale
                try:
                    slope, intercept, r_value, p_value, std_err = sp.stats.linregress(log_x, log_y)
                    # Compute line of best-fit
                    log_y_fit = slope * log_x + intercept

                    # 3a. Plot data (Log-Log scale with the line best-fit)
                    ax, i = plot_axis(i, "Log-Log Plot of", plot_err=False)
                    ax.plot(log_x, log_y, label='Data', color='b', marker='s', markersize=3)
                    ax.plot(log_x, log_y_fit, label=f'Fit: slope={slope:.2f}, $R^2$={r_value ** 2:.3f}', color='r')
                    ax.legend()
                    """i = i + 1
                    ax = fig.add_subplot(2, 2, i)
                    # ax.plot(x_values, y_values, 'b.', markersize=3)
                    ax.plot(log_x, log_y, label='Data', color='b', marker='s', markersize=3)
                    ax.plot(log_x, log_y_fit, label=f'Fit: slope={slope:.2f}, $R^2$={r_value ** 2:.3f}', color='r')
                    ax.set_title(f"Log-Log Plot of Nodes vs {y_title}", fontsize=10)
                    ax.set(xlabel='No. of Nodes (log scale)', ylabel=f'{param_name} (log scale)')
                    ax.legend()"""
                except Exception as e:
                    print(f"Log-Log Error: {e}")
                    pass

                # 2b. Compute the line of best-fit on our data according to our power-law model
                try:
                    init_params = [1.0, 1.0]  # initial guess for [a, k]
                    optimal_params: np.ndarray = sp.optimize.curve_fit(power_law_model, x_avg, y_avg, p0=init_params)[0]
                    a_fit, k_fit = float(optimal_params[0]), float(optimal_params[1])
                    # print(f"Fitted parameters: a = {a_fit:.4f}, k = {k_fit:.4f}")
                    # Generate points for the best-fit curve
                    y_fit_pwr = power_law_model(x_fit, a_fit, k_fit)

                    # 3b. Plot data (power-law best fit)
                    ax, i = plot_axis(i, "Power Law Fit and Plot of")
                    ax.plot(x_fit, y_fit_pwr, label=f'Fit: $y = ax^{{-k}}$\n$a={a_fit:.2f}, k={k_fit:.2f}$',
                            color='red')
                    ax.legend()
                    """i = i + 1
                    ax = fig.add_subplot(2, 2, i)
                    ax.errorbar(x_avg, y_avg, xerr=x_err, yerr=y_err, label='Data', color='b', capsize=4, marker='s',
                                markersize=4, linewidth=1, linestyle='-')
                    ax.plot(x_fit, y_fit_pwr, label=f'Fit: $y = ax^{{-k}}$\n$a={a_fit:.2f}, k={k_fit:.2f}$',
                            color='red')
                    ax.set_title(f"Nodes vs {y_title}", fontsize=10)
                    ax.set(xlabel='No. of Nodes', ylabel=f'{param_name}')
                    ax.legend()"""
                except Exception as e:
                    print(f"Power Law Error: {e}")
                    pass

                # 2c. Compute the line of best-fit according to our truncated power-law model
                try:
                    init_params_cutoff = [1.0, 1.0, 0.1]
                    opt_params_cutoff: np.ndarray = \
                    sp.optimize.curve_fit(truncated_power_law_model, x_avg, y_avg, p0=init_params_cutoff)[0]
                    a_fit_cut, k_fit_cut, c_fit_cut = float(opt_params_cutoff[0]), float(opt_params_cutoff[1]), float(
                        opt_params_cutoff[2])
                    # Generate points for the best-fit curve
                    y_fit_cut = truncated_power_law_model(x_fit, a_fit_cut, k_fit_cut, c_fit_cut)
                    print(f"Fitted parameters: a={a_fit_cut:.2f}, k={k_fit_cut:.2f}, c={c_fit_cut:.2f}")

                    # 3c. Plot data (truncated power-law best fit)
                    ax, i = plot_axis(i, "Truncated Power Law Fit and Plot of")
                    ax.plot(x_fit, y_fit_cut,
                            label=f'Fit: $y = ax^{{-k}}*exp(-c*x)$\n$a={a_fit_cut:.2f}, k={k_fit_cut:.2f}, c={c_fit_cut:.2f}$',
                            color='red')
                    ax.legend()
                    """i = i + 1
                    ax = fig.add_subplot(2, 2, i)
                    ax.errorbar(x_avg, y_avg, xerr=x_err, yerr=y_err, label='Data', color='b', capsize=4, marker='s',
                                markersize=4, linewidth=1, linestyle='-')
                    ax.plot(x_fit, y_fit_cut,
                            label=f'Fit: $y = ax^{{-k}}*exp(-c*x)$\n$a={a_fit_cut:.2f}, k={k_fit_cut:.2f}, c={c_fit_cut:.2f}$',
                            color='red')
                    ax.set_title(f"Nodes vs {y_title}", fontsize=10)
                    ax.set(xlabel='No. of Nodes', ylabel=f'{param_name}')
                    ax.legend()"""
                except Exception as e:
                    print(f"Truncated Power Law Error: {e}")
                    pass

                # 2d. Compute best-fit, assuming Log-Normal dependence on X
                try:
                    init_params_log = [1.0, 1.0, 10]
                    opt_params_log: np.ndarray = \
                    sp.optimize.curve_fit(lognormal_model, x_avg, y_avg, p0=init_params_log,
                                          bounds=([0, 0, 0], [np.inf, np.inf, np.inf]), maxfev=1000)[0]
                    mu_fit, sigma_fit, a_log_fit = float(opt_params_log[0]), float(opt_params_log[1]), float(
                        opt_params_log[2])
                    # Generate predicted points for the best-fit curve
                    y_fit_ln = lognormal_model(x_fit, mu_fit, sigma_fit, a_log_fit)

                    # 3c. Plot data (Log-normal distribution best fit)
                    ax, i = plot_axis(i, "Log-Normal Fit and Plot of")
                    ax.plot(x_fit, y_fit_ln,
                            label=f'Fit: log-normal shape\n$\\mu={mu_fit:.2f}$, $\\sigma={sigma_fit:.2f}$',
                            color='red')
                    ax.legend()
                    """i = i + 1
                    ax = fig.add_subplot(2, 2, i)
                    ax.errorbar(x_avg, y_avg, xerr=x_err, yerr=y_err, label='Data', color='b', capsize=4, marker='s',
                                markersize=4, linewidth=1, linestyle='-')
                    ax.plot(x_fit, y_fit_ln,
                            label=f'Fit: log-normal shape\n$\\mu={mu_fit:.2f}$, $\\sigma={sigma_fit:.2f}$',
                            color='red')
                    ax.set_title(f"Fit Assuming Log-Normal Dependence on\n Nodes vs {y_title}", fontsize=10)
                    ax.set(xlabel='No. of Nodes', ylabel=f'{param_name}')
                    ax.legend()"""
                except Exception as e:
                    print(f"Log Normal Dependence Error: {e}")
                    pass

            # Navigate to the next subplot
            if (i + 1) > 1:
                figs.append(fig)
                fig = plt.Figure(figsize=(8.5, 11), dpi=300)
                i = 0

        figs.append(fig) if i <= 4 else None
        return figs

    @staticmethod
    def write_to_pdf(sgt_obj, update_func=None):
        """
        Write results to a PDF file.

        Args:
            sgt_obj: StructuralGT object with calculated GT parameters
            update_func: Callable for progress updates (e.g., update_func(percentage, message))

        Returns:
            True if the PDF file is written successfully, otherwise False
        """
        try:
            if update_func:
                update_func(98, "Writing PDF...")

            filename, output_location = sgt_obj.ntwk_p.get_filenames()
            pdf_filename = filename + "_SGT_results.pdf"
            pdf_file = os.path.join(output_location, pdf_filename)

            if not sgt_obj.plot_figures:
                raise ValueError("No figures available to write to PDF.")

            with PdfPages(pdf_file) as pdf:
                for fig in sgt_obj.plot_figures:
                    pdf.savefig(fig)

            # if update_func:
            #    update_func(100, "GT PDF successfully generated!")
            return True
        except Exception as err:
            logging.exception("GT Computation Error: %s", err, extra={'user': 'SGT Logs'})
            if update_func:
                update_func(-1, "Error occurred while trying to write to PDF.")
            return False

    @staticmethod
    def safe_run_analyzer(sgt_obj, update_func):
        """
        Safely compute GT metrics without raising exceptions or crushing app.

        Args:
            sgt_obj: StructuralGT object with calculated GT parameters
            update_func: Callable for progress updates (e.g., update_func(percentage, message))
        """
        try:
            # Add Listeners
            sgt_obj.add_listener(update_func)

            sgt_obj.run_analyzer()
            if sgt_obj.abort:
                raise AbortException("Process aborted")

            # Cleanup - remove listeners
            sgt_obj.remove_listener(update_func)
            return True, sgt_obj
        except AbortException:
            update_func(-1, "Task aborted by user or a fatal error occurred!")
            sgt_obj.remove_listener(update_func)
            return False, None
        except Exception as err:
            update_func(-1, "Error encountered! Try again")
            logging.exception("Error: %s", err, extra={'user': 'SGT Logs'})
            # Clean up listeners before exiting
            sgt_obj.remove_listener(update_func)
            return False, None

    @staticmethod
    def safe_run_multi_analyzer(sgt_objs, update_func):
        """
        Safely compute GT metrics of multiple images without raising exceptions or crushing the app.

        Args:
            sgt_objs: List of StructuralGT objects with calculated GT parameters
            update_func: Callable for progress updates (e.g., update_func(percentage, message))
        """
        try:
            i = 0
            keys_list = list(sgt_objs.keys())
            for key in keys_list:
                sgt_obj = sgt_objs[key]

                status_msg = f"Analyzing Image: {(i + 1)} / {len(sgt_objs)}"
                update_func(101, status_msg)

                start = time.time()
                success, new_sgt = GraphAnalyzer.safe_run_analyzer(sgt_obj, update_func)
                # TerminalApp.is_aborted(sgt_obj)
                if success:
                    GraphAnalyzer.write_to_pdf(new_sgt, update_func)
                end = time.time()

                i += 1
                num_cores = get_num_cores()
                sel_batch = sgt_obj.ntwk_p.get_selected_batch()
                graph_obj = sel_batch.graph_obj
                output = status_msg + "\n" + f"Run-time: {str(end - start)}  seconds\n"
                output += "Number of cores: " + str(num_cores) + "\n"
                output += "Results generated for: " + sgt_obj.ntwk_p.img_path + "\n"
                output += "Node Count: " + str(graph_obj.nx_graph.number_of_nodes()) + "\n"
                output += "Edge Count: " + str(graph_obj.nx_graph.number_of_edges()) + "\n"
                filename, out_dir = sgt_obj.ntwk_p.get_filenames()
                out_file = os.path.join(out_dir, filename + '-v2_results.txt')
                write_txt_file(output, out_file)
                logging.info(output, extra={'user': 'SGT Logs'})
            return sgt_objs
        except AbortException:
            update_func(-1, "Task aborted by user or a fatal error occurred!")
            return None
        except Exception as err:
            update_func(-1, "Error encountered! Try again")
            logging.exception("Error: %s", err, extra={'user': 'SGT Logs'})
            return None
