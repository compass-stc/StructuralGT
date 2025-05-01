# SPDX-License-Identifier: GNU GPL v3

"""
Loads default configurations from 'configs.ini' file
"""

import os
import sys
import socket
import platform
import logging
import subprocess
import configparser


def load_img_configs():
    """Image Detection settings"""

    options_img = {
        "threshold_type": {"id": "threshold_type", "type": "binary-filter", "text": "", "visible": 1, "value": 1 },
        "global_threshold_value": {"id": "global_threshold_value", "type": "binary-filter", "text": "", "visible": 1, "value": 127 },
        "adaptive_local_threshold_value": {"id": "adaptive_local_threshold_value", "type": "binary-filter", "text": "", "visible": 1, "value": 11 },
        "otsu": {"id": "otsu", "type": "binary-filter", "text": "", "visible": 0, "value": 0},
        "apply_dark_foreground": {"id": "apply_dark_foreground", "type": "binary-filter", "text": "", "visible": 1, "value": 0},

        "apply_autolevel": {"id": "apply_autolevel", "type": "image-filter", "text": "Autolevel", "value": 0,
                            "dataId": "autolevel_blurring_size", "dataValue": 3, "minValue": 1, "maxValue": 7, "stepSize": 2},
        "apply_gaussian_blur": {"id": "apply_gaussian_blur", "type": "image-filter", "text": "Gaussian", "value": 0,
                                "dataId": "gaussian_blurring_size", "dataValue": 3, "minValue": 1, "maxValue": 7, "stepSize": 2 },
        "apply_laplacian_gradient": {"id": "apply_laplacian_gradient", "type": "image-filter", "text": "Laplacian",
                                     "value": 0, "dataId": "laplacian_kernel_size", "dataValue": 3, "minValue": 1, "maxValue": 7,  "stepSize": 2 },
        "apply_lowpass_filter": {"id": "apply_lowpass_filter", "type": "image-filter", "text": "Lowpass", "value": 0,
                                 "dataId": "lowpass_window_size", "dataValue": 10, "minValue": 0, "maxValue": 1000,  "stepSize": 1 },
        "apply_gamma": {"id": "apply_gamma", "type": "image-filter", "text": "LUT Gamma", "value": 1, "dataId": "adjust_gamma",
                        "dataValue": 1.0, "minValue": 0.01, "maxValue": 5.0, "stepSize": 0.01  },
        "apply_sobel_gradient": {"id": "apply_sobel_gradient", "type": "image-filter", "text": "Sobel", "value": 0,
                                 "dataId": "sobel_kernel_size", "dataValue": 3, "minValue": 1, "maxValue": 7,  "stepSize": 2 },
        "apply_median_filter": {"id": "apply_median_filter", "type": "image-filter", "text": "Median", "value": 0 },
        "apply_scharr_gradient": {"id": "apply_scharr_gradient", "type": "image-filter", "text": "Scharr", "value": 0},

        "brightness_level": {"id": "brightness_level", "type": "image-control", "text": "Brightness", "value": 0 },
        "contrast_level": {"id": "contrast_level", "type": "image-control", "text": "Contrast", "value": 0 },

        "scale_value_nanometers": {"id": "scale_value_nanometers", "type": "image-property", "text": "Scalebar (nm)", "visible": 1, "value": 1.0 },
        "scalebar_pixel_count": {"id": "scalebar_pixel_count", "type": "image-property", "text": "Scalebar Pixel Count", "visible": 1, "value": 0 },
        "resistivity": {"id": "resistivity", "type": "image-property", "text": "Resistivity (<html>&Omega;</html>m)", "visible": 1, "value": 1.0 },
        "pixel_width": {"id": "pixel_width", "type": "image-property", "text": "", "visible": 0, "value": 1.0},  # * (10**-9)  # 1 nanometer

        "save_images": {"id": "save_images", "type": "file-options", "text": "Save All Images", "visible": 1, "value": 0},
    }

    # Load configuration from the file
    config = configparser.ConfigParser()
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = 'configs.ini'
        config_file = os.path.join(script_dir, config_path)
        config.read(config_file)

        options_img["threshold_type"]["value"] = int(config.get('filter-settings', 'threshold_type'))
        options_img["global_threshold_value"]["value"] = int(config.get('filter-settings', 'global_threshold_value'))
        options_img["adaptive_local_threshold_value"]["value"] = int(config.get('filter-settings', 'adaptive_local_threshold_value'))
        options_img["apply_dark_foreground"]["value"] = int(config.get('filter-settings', 'apply_dark_foreground'))

        options_img["apply_gamma"]["value"] = float(config.get('filter-settings', 'apply_gamma'))
        options_img["apply_gamma"]["dataValue"] = float(config.get('filter-settings', 'adjust_gamma'))
        options_img["apply_autolevel"]["value"] = int(config.get('filter-settings', 'apply_autolevel'))
        options_img["apply_autolevel"]["dataValue"] = int(config.get('filter-settings', 'blurring_window_size'))
        options_img["apply_laplacian_gradient"]["value"] = int(config.get('filter-settings', 'apply_laplacian_gradient'))
        options_img["apply_laplacian_gradient"]["dataValue"] = 3
        options_img["apply_sobel_gradient"]["value"] = int(config.get('filter-settings', 'apply_sobel_gradient'))
        options_img["apply_sobel_gradient"]["dataValue"] = 3
        options_img["apply_gaussian_blur"]["value"] = int(config.get('filter-settings', 'apply_gaussian_blur'))
        options_img["apply_gaussian_blur"]["dataValue"] = int(config.get('filter-settings', 'blurring_window_size'))
        options_img["apply_lowpass_filter"]["value"] = int(config.get('filter-settings', 'apply_lowpass_filter'))
        options_img["apply_lowpass_filter"]["dataValue"] = int(config.get('filter-settings', 'filter_window_size'))

        options_img["apply_scharr_gradient"]["value"] = int(config.get('filter-settings', 'apply_scharr_gradient'))
        options_img["apply_median_filter"]["value"] = int(config.get('filter-settings', 'apply_median_filter'))

        options_img["brightness_level"]["value"] = int(config.get('filter-settings', 'brightness_level'))
        options_img["contrast_level"]["value"] = int(config.get('filter-settings', 'contrast_level'))
        options_img["scale_value_nanometers"]["value"] = float(config.get('filter-settings', 'scale_value_nanometers'))
        options_img["scalebar_pixel_count"]["value"] = int(config.get('filter-settings', 'scalebar_pixel_count'))
        options_img["resistivity"]["value"] = float(config.get('filter-settings', 'resistivity'))

        options_img["save_images"]["value"] = int(config.get('file-options', 'save_images'))

        return options_img
    except configparser.NoSectionError:
        return options_img


def load_gte_configs():
    """Graph Extraction Settings"""

    options_gte = {
        "has_weights": {"id": "has_weights", "type": "graph-extraction", "text": "Add Weights", "value": 0,
                        "items": [
                            {"id": "DIA", "text": "by diameter", "value": 1},
                            {"id": "AREA", "text": "by area", "value": 0},
                            {"id": "LEN", "text": "by length", "value": 0},
                            {"id": "ANGLE", "text": "by angle", "value": 0},
                            {"id": "INV-LEN", "text": "by inverse-length", "value": 0},
                            {"id": "FIX-CON", "text": "by conductance", "value": 0},
                            {"id": "RES", "text": "by resistance", "value": 0},
                        ]},
        "merge_nearby_nodes": {"id": "merge_nearby_nodes", "type": "graph-extraction", "text": "Merge Nearby Nodes", "value": 1},
        "prune_dangling_edges": {"id": "prune_dangling_edges", "type": "graph-extraction", "text": "Prune Dangling Edges", "value": 1},
        "remove_disconnected_segments": {"id": "remove_disconnected_segments", "type": "graph-extraction", "text": "Remove Disconnected Segments", "value": 1, "items": [{"id": "remove_object_size", "text": "", "value": 500}]},
        "remove_self_loops": {"id": "remove_self_loops", "type": "graph-extraction", "text": "Remove Self Loops", "value": 1},
        "display_node_id": {"id": "display_node_id", "type": "graph-extraction", "text": "Display Node ID", "value": 0},

        "export_edge_list": {"id": "export_edge_list", "type": "file-options", "text": "Export Edge List", "value": 0},
        "export_as_gexf": {"id": "export_as_gexf", "type": "file-options", "text": "Export as gexf", "value": 0},
        "export_adj_mat": {"id": "export_adj_mat", "type": "file-options", "text": "Export Adjacency Matrix", "value": 0},
        "export_as_gsd": {"id": "export_as_gsd", "type": "file-options", "text": "Export as GSD/HOOMD", "value": 0},
    }

    # Load configuration from the file
    config = configparser.ConfigParser()
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = 'configs.ini'
        config_file = os.path.join(script_dir, config_path)
        config.read(config_file)

        options_gte["merge_nearby_nodes"]["value"] = int(config.get('extraction-settings', 'merge_nearby_nodes'))
        options_gte["prune_dangling_edges"]["value"] = int(config.get('extraction-settings', 'prune_dangling_edges'))
        options_gte["remove_disconnected_segments"]["value"] = int(
            config.get('extraction-settings', 'remove_disconnected_segments'))
        options_gte["remove_disconnected_segments"]["items"][0]["value"] = int(config.get('extraction-settings', 'remove_object_size'))
        options_gte["remove_self_loops"]["value"] = int(config.get('extraction-settings', 'remove_self_loops'))
        options_gte["has_weights"]["value"] = int(config.get('extraction-settings', 'add_weights'))
        weight_type = str(config.get('extraction-settings', 'weight_type'))
        for i in range(len(options_gte["has_weights"]["items"])):
            options_gte["has_weights"]["items"][i]["value"] = 1 if options_gte["has_weights"]["items"][i]["id"] == weight_type else 0
        options_gte["display_node_id"]["value"] = int(config.get('extraction-settings', 'display_node_id'))
        options_gte["export_edge_list"]["value"] = int(config.get('extraction-settings', 'export_edge_list'))
        options_gte["export_as_gexf"]["value"] = int(config.get('extraction-settings', 'export_as_gexf'))
        options_gte["export_adj_mat"]["value"] = int(config.get('extraction-settings', 'export_adj_mat'))
        options_gte["export_as_gsd"]["value"] = int(config.get('extraction-settings', 'export_as_gsd'))

        return options_gte
    except configparser.NoSectionError:
        return options_gte


def load_gtc_configs():
    """Networkx Calculation Settings"""

    options_gtc = {
        "display_heatmaps": {"id": "display_heatmaps", "text": "Plot Heatmaps", "value": 1},
        "display_degree_histogram": {"id": "display_degree_histogram", "text": "Average Degree", "value": 1},
        "compute_network_diameter": {"id": "compute_network_diameter", "text": "Network Diameter", "value": 1},
        "compute_graph_density": {"id": "compute_graph_density", "text": "Graph Density", "value": 1},
        "compute_wiener_index": {"id": "compute_wiener_index", "text": "Wiener Index", "value": 1},
        "compute_avg_node_connectivity": {"id": "compute_avg_node_connectivity", "text": "Average Node Connectivity", "value": 0},
        "compute_global_efficiency": {"id": "compute_global_efficiency", "text": "Global Coefficient", "value": 1},
        "compute_avg_clustering_coef": {"id": "compute_avg_clustering_coef", "text": "Average Clustering Coefficient", "value": 1},
        "compute_assortativity_coef": {"id": "compute_assortativity_coef", "text": "Assortativity Coefficient", "value": 1},
        "display_betweenness_centrality_histogram": {"id": "display_betweenness_centrality_histogram", "text": "Betweenness Centrality", "value": 1},
        "display_closeness_centrality_histogram": {"id": "display_closeness_centrality_histogram", "text": "Closeness Centrality", "value": 1},
        "display_eigenvector_centrality_histogram": {"id": "display_eigenvector_centrality_histogram", "text": "Eigenvector Centrality", "value": 1},
        "display_ohms_histogram": {"id": "display_ohms_histogram", "text": "Ohms Centrality", "value": 0},
        #"display_currentflow_histogram": {"id": "display_currentflow_histogram", "text": "Current Flow Betweenness Centrality", "value": 0},
        "display_edge_angle_centrality_histogram": {"id": "display_edge_angle_centrality_histogram", "text": "Edge Angle Centrality", "value": 0},
        #"compute_graph_conductance": {"id": "compute_graph_conductance", "text": "Graph Conductance", "value": 0},
        "display_percolation_histogram": {"id": "display_percolation_histogram", "text": "Percolation Centrality", "value": 0},
        #"compute_lang": {"id": "compute_lang", "text": "Programming Language", "value": 'Py'}
    }

    # Load configuration from the file
    config = configparser.ConfigParser()
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = 'configs.ini'
        config_file = os.path.join(script_dir, config_path)
        config.read(config_file)

        options_gtc["display_heatmaps"]["value"] = int(config.get('sgt-settings', 'display_heatmaps'))
        options_gtc["display_degree_histogram"]["value"] = int(config.get('sgt-settings', 'display_degree_histogram'))
        options_gtc["display_betweenness_centrality_histogram"]["value"] = int(config.get('sgt-settings', 'display_betweenness_centrality_histogram'))
        # options_gtc["display_current_flow_betweenness_centrality_histogram"]["value"] = int(
        #    config.get('sgt-settings', 'display_current_flow_betweenness_centrality_histogram'))
        options_gtc["display_closeness_centrality_histogram"]["value"] = int(config.get('sgt-settings', 'display_closeness_centrality_histogram'))
        options_gtc["display_eigenvector_centrality_histogram"]["value"] = int(config.get('sgt-settings', 'display_eigenvector_centrality_histogram'))
        options_gtc["display_edge_angle_centrality_histogram"]["value"] = int(config.get('sgt-settings', 'display_edge_angle_centrality_histogram'))
        options_gtc["display_ohms_histogram"]["value"] = int(config.get('sgt-settings', 'display_ohms_histogram'))
        options_gtc["display_percolation_histogram"]["value"] = int(config.get('sgt-settings', 'display_percolation_histogram'))
        options_gtc["compute_avg_node_connectivity"]["value"] = int(config.get('sgt-settings', 'compute_avg_node_connectivity'))
        options_gtc["compute_graph_density"]["value"] = int(config.get('sgt-settings', 'compute_graph_density'))
        # options_gtc["compute_graph_conductance"]["value"] = int(config.get('sgt-settings', 'compute_graph_conductance'))
        options_gtc["compute_global_efficiency"]["value"] = int(config.get('sgt-settings', 'compute_global_efficiency'))
        options_gtc["compute_avg_clustering_coef"]["value"] = int(config.get('sgt-settings', 'compute_avg_clustering_coef'))
        options_gtc["compute_assortativity_coef"]["value"] = int(config.get('sgt-settings', 'compute_assortativity_coef'))
        options_gtc["compute_network_diameter"]["value"] = int(config.get('sgt-settings', 'compute_network_diameter'))
        options_gtc["compute_wiener_index"]["value"] = int(config.get('sgt-settings', 'compute_wiener_index'))
        # options_gtc["compute_lang"]["value"] = str(config.get('sgt-settings', 'compute_lang'))

        return options_gtc
    except configparser.NoSectionError:
        return options_gtc


def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        logging.info(f"Successfully installed {package}", extra={'user': 'SGT Logs'})
    except subprocess.CalledProcessError:
        logging.info(f"Failed to install {package}: ", extra={'user': 'SGT Logs'})


def detect_cuda_version():
    """Check if CUDA is installed and return its version."""
    try:
        output = subprocess.check_output(['nvcc', '--version']).decode()
        if 'release 12' in output:
            return '12'
        elif 'release 11' in output:
            return '11'
        else:
            return None
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.info(f"Please install 'NVIDIA GPU Computing Toolkit' via: https://developer.nvidia.com/cuda-downloads", extra={'user': 'SGT Logs'})
        return None


def is_connected(host="8.8.8.8", port=53, timeout=3):
    """Check if the system has an active internet connection."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False


def detect_cuda_and_install_cupy():
    try:
        import cupy
        logging.info(f"CuPy is already installed: {cupy.__version__}", extra={'user': 'SGT Logs'})
        return
    except ImportError:
        logging.info("CuPy is not installed.", extra={'user': 'SGT Logs'})

    if not is_connected():
        logging.info("No internet connection. Cannot install CuPy.", extra={'user': 'SGT Logs'})
        return

    # Handle macOS (Apple Silicon) - CPU only
    if platform.system() == "Darwin" and platform.processor().startswith("arm"):
        logging.info("Detected MacOS with Apple Silicon (M1/M2/M3). Installing CPU-only version of CuPy.", extra={'user': 'SGT Logs'})
        # install_package('cupy')  # CPU-only version
        return

    # Handle CUDA systems (Linux/Windows with GPU)
    cuda_version = detect_cuda_version()

    if cuda_version:
        logging.info(f"CUDA detected: {cuda_version}", extra={'user': 'SGT Logs'})
        if cuda_version == '12':
            install_package('cupy-cuda12x')
        elif cuda_version == '11':
            install_package('cupy-cuda11x')
        else:
            logging.info("CUDA version not supported. Installing CPU-only CuPy.", extra={'user': 'SGT Logs'})
            install_package('cupy')
    else:
        # No CUDA found, fall back to the CPU-only version
        logging.info("CUDA not found. Installing CPU-only CuPy.", extra={'user': 'SGT Logs'})
        install_package('cupy')

    # Proceed with installation if connected
    cuda_version = detect_cuda_version()
    if cuda_version == '12':
        install_package('cupy-cuda12x')
    elif cuda_version == '11':
        install_package('cupy-cuda11x')
    else:
        logging.info("No CUDA detected or NVIDIA GPU Toolkit not installed. Installing CPU-only CuPy.", extra={'user': 'SGT Logs'})
        install_package('cupy')
