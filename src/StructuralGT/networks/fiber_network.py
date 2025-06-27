# SPDX-License-Identifier: GNU GPL v3

"""
Builds a graph network from nanoscale microscopy images.
"""

import os
import igraph
import itertools
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from PIL import Image, ImageQt
from cv2.typing import MatLike
from ovito.vis import Viewport
from ovito.data import DataCollection, Particles
from ovito.pipeline import StaticSource, Pipeline

from .sknw_mod import build_sknw
from ..utils.progress_update import ProgressUpdate
from ..networks.graph_skeleton import GraphSkeleton
from ..utils.config_loader import load_gte_configs
from ..utils.sgt_utils import write_csv_file, write_gsd_file


class FiberNetworkBuilder(ProgressUpdate):
    """
    A class for builds a graph network from microscopy images and stores is as a NetworkX object.

    """

    def __init__(self, cfg_file=""):
        """
        A class for builds a graph network from microscopy images and stores is as a NetworkX object.

        Args:
            cfg_file (str): configuration file path

        """
        super(FiberNetworkBuilder, self).__init__()
        self.configs: dict = load_gte_configs(cfg_file)  # graph extraction parameters and options.
        self.props: list = []
        self.img_ntwk: MatLike | None = None
        self.nx_giant_graph: nx.Graph | None = None
        self.nx_graph: nx.Graph | None = None
        self.ig_graph: igraph.Graph | None = None
        self.gsd_file: str | None = None
        self.skel_obj: GraphSkeleton | None = None

    def fit_graph(self, save_dir: str, img_bin: MatLike = None, is_img_2d: bool = True, px_width_sz: float = 1.0, rho_val: float = 1.0, image_file: str = "img"):
        """
        Execute a function that builds a NetworkX graph from the binary image.

        :param save_dir: Directory to save the graph to.
        :param img_bin: A binary image for building Graph Skeleton for the NetworkX graph.
        :param is_img_2d: Whether the image is 2D or 3D otherwise.
        :param px_width_sz: Width of a pixel in nanometers.
        :param rho_val: Resistivity coefficient/value of the material.
        :param image_file: Filename of the binary image.
        :return:
        """

        if self.abort:
            self.update_status([-1, "Task aborted by due to an error. If problem with graph: change/apply different "
                                    "image/binary filters and graph options. OR change brightness/contrast"])
            return

        self.update_status([50, "Extracting the graph network..."])
        success = self.extract_graph(image_bin=img_bin, is_img_2d=is_img_2d, px_size=px_width_sz, rho_val=rho_val)
        if not success:
            self.update_status([-1, "Problem encountered, provide GT parameters"])
            self.abort = True
            return

        self.update_status([75, "Verifying graph network..."])
        if self.nx_graph.number_of_nodes() <= 0:
            self.update_status([-1, "Problem generating graph (change image/binary filters)"])
            self.abort = True
            return

        self.update_status([77, "Retrieving graph properties..."])
        self.props = self.get_graph_props()

        self.update_status([90, "Saving graph network..."])
        # Save graph to GSD/HOOMD - For OVITO rendering
        self.configs["export_as_gsd"]["value"] = 1
        self.save_graph_to_file(image_file, save_dir)

    def reset_graph(self):
        """
        Erase the existing data stored in the object.
        :return:
        """
        self.nx_graph, self.ig_graph, self.img_ntwk = None, None, None

    def extract_graph(self, image_bin: MatLike = None, is_img_2d: bool = True, px_size: float = 1.0, rho_val: float = 1.0):
        """
        Build a skeleton from the image and use the skeleton to build a NetworkX graph.

        :param image_bin: Binary image from which the skeleton will be built and graph drawn.
        :param is_img_2d: Whether the image is 2D or 3D otherwise.
        :param px_size: Width of a pixel in nanometers.
        :param rho_val: Resistivity coefficient/value of the material.
        :return:
        """

        if image_bin is None:
            return False

        opt_gte = self.configs
        if opt_gte is None:
            return False

        self.update_status([51, "Build graph skeleton from binary image..."])
        graph_skel = GraphSkeleton(image_bin, opt_gte, is_2d=is_img_2d, progress_func=self.update_status)
        self.skel_obj = graph_skel
        img_skel = graph_skel.skeleton

        self.update_status([60, "Creating graph network..."])
        # nx_graph = sknw.build_sknw(img_skel)
        nx_graph = build_sknw(img_skel)

        if opt_gte["remove_self_loops"]["value"]:
            self.update_status([64, "Removing self loops from graph network..."])

        self.update_status([66, "Assigning weights to graph network..."])
        for (s, e) in nx_graph.edges():
            if opt_gte["remove_self_loops"]["value"]:
                # Removing all instances of edges where the start and end are the same, or "self-loops"
                if s == e:
                    nx_graph.remove_edge(s, e)
                    continue

            # 'sknw' library stores the length of edge as 'weight', we create an attribute 'length', and update 'weight'
            nx_graph[s][e]['length'] = nx_graph[s][e]['weight']
            ge = nx_graph[s][e]['pts']

            if opt_gte["has_weights"]["value"] == 1:
                # We update 'weight'
                wt_type = self.get_weight_type()
                weight_options = FiberNetworkBuilder.get_weight_options()
                pix_width, pix_angle, wt = graph_skel.assign_weights(ge, wt_type, weight_options=weight_options,
                                                                         pixel_dim=px_size, rho_dim=rho_val)
            else:
                pix_width, pix_angle, wt = graph_skel.assign_weights(ge, None)
                del nx_graph[s][e]['weight']            # delete 'weight'
            nx_graph[s][e]['width'] = pix_width
            nx_graph[s][e]['angle'] = pix_angle
            nx_graph[s][e]['weight'] = wt
            # print(f"{nx_graph[s][e]}\n")
        self.nx_graph = nx_graph
        self.ig_graph = igraph.Graph.from_networkx(nx_graph)
        return True

    def plot_graph_network(self, image_arr: MatLike, giant_only: bool = False, plot_nodes: bool = False, a4_size: bool = False):
        """
        Creates a plot figure of the graph network. It draws all the edges and nodes of the graph.

        :param image_arr: Slides of 2D images to be used to draw the network.
        :param giant_only: If True, only the giant graph is identified and drawn.
        :param plot_nodes: Make the graph's node plot figure.
        :param a4_size: Decision if to create an A4 size plot figure.

        :return:
        """

        if self.nx_graph is None:
            return None

        # Fetch the graph and config options
        if giant_only:
            nx_graph = self.nx_giant_graph
        else:
            nx_graph = self.nx_graph
        show_node_id = (self.configs["display_node_id"]["value"] == 1)

        # Fetch a single 2D image
        if image_arr is None:
            return None

        # Create the plot figure(s)
        fig_grp = FiberNetworkBuilder.plot_graph_edges(image_arr, nx_graph, plot_nodes=plot_nodes, show_node_id=show_node_id)
        fig = fig_grp[0]
        if a4_size:
            plt_title = "Graph Node Plot" if plot_nodes else "Graph Edge Plot"
            fig.set_size_inches(8.5, 11)
            fig.set_dpi(400)
            ax = fig.axes[0]
            ax.set_title(plt_title)
            # This moves the Axes to start: 5% from the left, 5% from the bottom,
            # and have a width and height: 80% of the figure.
            # [left, bottom, width, height]
            ax.set_position([0.05, 0.05, 0.9, 0.9])
        return fig

    def get_config_info(self):
        """
        Get the user selected parameters and options information.
        :return:
        """

        opt_gte = self.configs

        run_info = "***Graph Extraction Configurations***\n"
        if opt_gte["has_weights"]["value"] == 1:
            wt_type = self.get_weight_type()
            run_info += f"Weight Type: {FiberNetworkBuilder.get_weight_options().get(wt_type)} || "
        if opt_gte["merge_nearby_nodes"]["value"]:
            run_info += "Merge Nodes || "
        if opt_gte["prune_dangling_edges"]["value"]:
            run_info += "Prune Dangling Edges || "
        run_info = run_info[:-3] + '' if run_info.endswith('|| ') else run_info
        run_info += "\n"
        if opt_gte["remove_disconnected_segments"]["value"]:
            run_info += f"Remove Objects of Size = {opt_gte["remove_disconnected_segments"]["items"][0]["value"]} || "
        if opt_gte["remove_self_loops"]["value"]:
            run_info += "Remove Self Loops || "
        run_info = run_info[:-3] + '' if run_info.endswith('|| ') else run_info

        return run_info

    def get_graph_props(self):
        """
        A method that retrieves graph properties and stores them in a list-array.

        Returns: list of graph properties
        """

        # 1. Identify the subcomponents (graph segments) that make up the entire NetworkX graph.
        self.update_status([78, "Identifying graph subcomponents..."])
        graph = self.nx_graph.copy()
        connected_components = list(nx.connected_components(graph))
        if not connected_components:  # In case the graph is empty
            connected_components = []
        sub_graphs = [graph.subgraph(c).copy() for c in connected_components]
        giant_graph = max(sub_graphs, key=lambda g: g.number_of_nodes())
        num_graphs = len(sub_graphs)
        connect_ratio = giant_graph.number_of_nodes() / graph.number_of_nodes()

        # 2. Update with the giant graph
        self.nx_giant_graph = giant_graph
        # self.ig_graph = igraph.Graph.from_networkx(giant_graph)

        # 3. Populate graph properties
        self.update_status([80, "Storing graph properties..."])
        props = [
            ["Weight Type", str(FiberNetworkBuilder.get_weight_options().get(self.get_weight_type()))],
            ["Edge Count", str(graph.number_of_edges())],
            ["Node Count", str(graph.number_of_nodes())],
            ["Graph Count", str(len(connected_components))],
            ["Sub-graph Count", str(num_graphs)],
            ["Giant graph ratio", f"{round((connect_ratio * 100), 3)}%"]]
        return props

    def get_weight_type(self):
        wt_type = None  # Default weight
        if self.configs["has_weights"]["value"] == 0:
            return wt_type

        for i in range(len(self.configs["has_weights"]["items"])):
            if self.configs["has_weights"]["items"][i]["value"]:
                wt_type = self.configs["has_weights"]["items"][i]["id"]
        return wt_type

    def save_graph_to_file(self, filename: str, out_dir: str):
        """
        Save graph data into files.

        :param filename: The filename to save the data to.
        :param out_dir: The directory to save the data to.
        :return:
        """

        nx_graph = self.nx_graph.copy()
        opt_gte = self.configs

        g_filename = filename + "_graph.gexf"
        el_filename = filename + "_EL.csv"
        adj_filename = filename + "_adj.csv"
        gsd_filename = filename + "_skel.gsd"
        gexf_file = os.path.join(out_dir, g_filename)
        csv_file = os.path.join(out_dir, el_filename)
        adj_file = os.path.join(out_dir, adj_filename)

        if opt_gte["export_adj_mat"]["value"] == 1:
            adj_mat = nx.adjacency_matrix(self.nx_graph).todense()
            np.savetxt(str(adj_file), adj_mat, delimiter=",")

        if opt_gte["export_edge_list"]["value"] == 1:
            if opt_gte["has_weights"]["value"] == 1:
                fields = ['Source', 'Target', 'Weight', 'Length']
                el = nx.generate_edgelist(nx_graph, delimiter=',', data=True)
                write_csv_file(csv_file, fields, el)
            else:
                fields = ['Source', 'Target']
                el = nx.generate_edgelist(nx_graph, delimiter=',', data=False)
                write_csv_file(csv_file, fields, el)

        if opt_gte["export_as_gexf"]["value"] == 1:
            # deleting extraneous info and then exporting the final skeleton
            for (x) in nx_graph.nodes():
                del nx_graph.nodes[x]['pts']
                del nx_graph.nodes[x]['o']
            for (s, e) in nx_graph.edges():
                del nx_graph[s][e]['pts']
            nx.write_gexf(nx_graph, gexf_file)

        if opt_gte["export_as_gsd"]["value"] == 1:
            self.gsd_file = os.path.join(out_dir, gsd_filename)
            if self.skel_obj.skeleton_3d is not None:
                write_gsd_file(self.gsd_file, self.skel_obj.skeleton_3d)

    @staticmethod
    def get_weight_options():
        """
        Returns the weight options for building the graph edges.

        :return:
        """
        weight_options = {
            'DIA': 'Diameter',
            'AREA': 'Area',  # surface area of edge
            'LEN': 'Length',
            'ANGLE': 'Angle',
            'INV_LEN': 'InverseLength',
            'VAR_CON': 'Conductance',  # with variable width
            'FIX_CON': 'FixedWidthConductance',
            'RES': 'Resistance',
            # '': ''
        }
        return weight_options

    @staticmethod
    def plot_graph_edges(image: MatLike, nx_graph: nx.Graph, node_distribution_data: list = None, plot_nodes: bool = False, show_node_id: bool = False, transparent: bool = False, line_width: float=1.5, node_marker_size: float = 3):
        """
        Plot graph edges on top of the image

        :param image: image to be superimposed with graph edges
        :param nx_graph: a NetworkX graph
        :param node_distribution_data: a list of node distribution data for a heatmap plot
        :param plot_nodes: whether to plot graph nodes or not
        :param show_node_id: if True, node IDs are displayed on the plot
        :param transparent: whether to draw the image with a transparent background
        :param line_width: each edge's line width
        :param node_marker_size: the size (diameter) of the node marker
        :return:
        """

        def plot_graph_nodes(node_ax):
            """
            Plot graph nodes on top of the image.
            :param node_ax: Matplotlib axes
            """

            node_list = list(nx_graph.nodes())
            gn = np.array([nx_graph.nodes[i]['o'] for i in node_list])

            if show_node_id:
                i = 0
                for x, y in zip(gn[:, coord_1], gn[:, coord_2]):
                    node_ax.annotate(str(i), (x, y), fontsize=5)
                    i += 1

            if node_distribution_data is not None:
                c_set = node_ax.scatter(gn[:, coord_1], gn[:, coord_2], s=node_marker_size, c=node_distribution_data, cmap='plasma')
                return c_set
            else:
                # c_set = node_ax.scatter(gn[:, coord_1], gn[:, coord_2], s=marker_size)
                node_ax.plot(gn[:, coord_1], gn[:, coord_2], 'b.', markersize=node_marker_size)
                return None

        def create_plt_axes(pos):
            """
            Create a matplotlib axes object.
            Args:
                pos: index position of image frame.

            Returns:

            """
            new_fig = plt.Figure()
            new_ax = new_fig.add_axes((0, 0, 1, 1))  # span the whole figure
            new_ax.set_axis_off()
            if transparent:
                new_ax.imshow(image[pos], cmap='gray', alpha=0)  # Alpha=0 makes image 100% transparent
            else:
                new_ax.imshow(image[pos], cmap='gray')
            return new_fig

        fig_group = {}
        # Create axes for the first frame of image (enough if it is 2D)
        fig = create_plt_axes(0)
        fig_group[0] = fig

        color_list = ['black', 'r', 'g', 'b', 'c', 'm', 'y', 'k']
        color_cycle = itertools.cycle(color_list)
        nx_components = list(nx.connected_components(nx_graph))
        for component in nx_components:
            color = next(color_cycle)
            sg = nx_graph.subgraph(component)

            for (s, e) in sg.edges():
                ge = sg[s][e]['pts']
                coord_1, coord_2 = 1, 0  # coordinates: (y, x)
                coord_3 = 0
                if ge.shape[1] == 3:
                    # image and graph are 3D (not 2D)
                    # 3D Coordinates are (x, y, z) ... assume that y and z are the same for 2D graphs and x is depth.
                    coord_1, coord_2, coord_3 = 2, 1, 0  # coordinates: (z, y, x)

                if coord_3 in fig_group and fig_group[coord_3] is not None:
                    fig = fig_group[coord_3]
                else:
                    fig = create_plt_axes(coord_3)
                    fig_group[coord_3] = fig
                ax = fig.get_axes()[0]
                ax.plot(ge[:, coord_1], ge[:, coord_2], color, linewidth=line_width)

        if plot_nodes:
            for idx, plt_fig in fig_group.items():
                ax = plt_fig.get_axes()[0]
                node_color_set = plot_graph_nodes(ax)
                if node_color_set is not None:
                    cbar = plt_fig.colorbar(node_color_set, ax=ax, orientation='vertical', label='Value')
                    # [left, bottom, width, height]
                    cbar.ax.set_position([0.82, 0.05, 0.05, 0.9])
        return fig_group

    # TO DELETE IT LATER
    def data_gen_function(self):
        """Populates OVITO's data with particles."""
        data = DataCollection()
        positions = np.asarray(np.where(np.asarray(self.skel_obj.skeleton_3d) != 0)).T
        particles = Particles()
        particles.create_property("Position", data=positions)
        data.objects.append(particles)
        return data

    # ONLY RUNS ON MAIN THREAD - TO BE DELETED
    def render_graph_to_image(self, bg_image=None, is_img_2d: bool = True):
        """
        Renders the graph network into an image; it can optionally superimpose the graph on the image.

        :param bg_image: Optional background image.
        :param is_img_2d: Whether the image is 2D or 3D otherwise.
        """
        if self.gsd_file is None:
            return None

        if bg_image is not None:
            # OVITO doesn’t directly support 3D numpy volumes as backgrounds
            bg_image = bg_image.squeeze()
            if not is_img_2d:
                # (visualize only one slice) Extract a middle slice from 3D grayscale volume
                mid_slice = bg_image[bg_image.shape[0] // 2]  # shape: (H, W)
            else:
                mid_slice = bg_image

            # Convert to RGB for PIL
            # bg_rgb = cv2.cvtColor(mid_slice, cv2.COLOR_GRAY2RGB)
            bg_pil = Image.fromarray(mid_slice).convert("RGB")

            # Set OVITO render size
            size = (bg_pil.width, bg_pil.height)
        else:
            size = (800, 600)
            bg_pil = None

        # Load OVITO pipeline and scene
        # pipeline = import_file(self.gsd_file)
        data = self.data_gen_function()
        # print(type(data))
        pipeline = Pipeline(source = StaticSource(data = data))
        pipeline.add_to_scene()

        vp = Viewport(type=Viewport.Type.Front, camera_dir=(2, 1, -1))
        vp.zoom_all(size)

        # Render to QImage without the alpha channel
        q_img = vp.render_image(size=size, alpha=True, background=(1, 1, 1))

        # Convert QImage to PIL Image
        pil_img = ImageQt.fromqimage(q_img).convert("RGB")

        if bg_pil is not None:
            # Overlay using simple blending (optional: adjust transparency)
            final_img = Image.blend(bg_pil, pil_img, alpha=0.5)
        else:
            final_img = pil_img
        return final_img
