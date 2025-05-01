# SPDX-License-Identifier: GNU GPL v3

"""
Terminal interface implementations
"""

import time
import os
import logging

from ..SGT.sgt_utils import get_num_cores
from ..SGT.network_processor import NetworkProcessor
from ..SGT.fiber_network import FiberNetworkBuilder
from ..SGT.graph_analyzer import GraphAnalyzer


def terminal_app():
    """
    Initializes and executes StructuralGT functions.
    :return:
    """
    configs = load_project_configs()

    alg = configs.algChoice
    num_cores = configs.numCores
    is_multi = configs.multiImage
    img_path = configs.filePath
    out_dir = configs.outputDir
    filenames = []

    try:
        # 1. Get correct number of CPU cores
        if num_cores > 1:
            pass
        else:
            num_cores = get_num_cores()

        # 2. Verify image file or image-dir
        if is_multi == 1:
            # Process multiple images in one folder
            # getting the file names and directory
            files = os.listdir(img_path)
            files = sorted(files)
            out_path = img_path
            for a_file in files:
                if a_file.endswith(('.tif', '.png', '.jpg', '.jpeg')):
                    print(a_file)
                    logging.info(a_file, extra={'user': 'SGT Logs'})
                    filenames.append(os.path.join(out_path, a_file))
            if len(filenames) <= 0:
                raise Exception("No workable images found! Files have to be either .tif, .png, or .jpg")
        else:
            # Process only a single image file
            # testing if file is a workable image
            if img_path.endswith(('.tif', '.png', '.jpg', '.jpeg')):
                if os.path.isfile(img_path):
                    filenames.append(img_path)
                else:
                    raise Exception("File does not exist! Select valid file path.")
            else:
                raise Exception("File has to be a .tif, .png, or .jpg")

        # 3. Verify output directory
        if not os.path.isdir(out_dir):
            path, _ = os.path.split(filenames[0])
            out_dir = path

        # 4. Run GT program
        start = time.time()
        if alg == 0:
            file_count = len(filenames)
            for i in range(file_count):
                print(f'Analyzing Image: {i+1}/{len(filenames)}')
                logging.info(f'Analyzing Image: {i+1}/{len(filenames)}', extra={'user': 'SGT Logs'})
                im_path = filenames[i]
                produce_metrics(im_path, out_dir)

                # updating the images completed
                print("Results generated for " + im_path)
                # print(f'Images Completed: {i+1}/{len(filenames)}')
                print("----------------\n\n")
        else:
            raise Exception("Wrong algorithm choice!")
        duration = time.time() - start
        out_line = "Run-time: " + str(duration) + " seconds\n"
        out_line += "Number of cores: " + str(num_cores) + '\n'
        print(out_line)
        logging.info(out_line, extra={'user': 'SGT Logs'})
    except PermissionError as error:
        print(error)
        logging.exception("Error: %s", error, extra={'user': 'SGT Logs'})


def produce_metrics(img_path, out_dir):
    """
    Executes StructuralGT functions that compute all the user selected metrics.

    Args:
        img_path (str): input image path.
        out_dir (str): directory path for storing results.
    Returns:
        None:
    """
    imp_obj = NetworkProcessor(img_path, out_dir)
    graph_obj = FiberNetworkBuilder(imp_obj)
    graph_obj.add_listener(print_progress)
    graph_obj.fit()

    metrics_obj = GraphAnalyzer(graph_obj)
    metrics_obj.add_listener(print_progress)
    metrics_obj.compute_gt_metrics()
    if graph_obj.configs.weighted_by_diameter:
        metrics_obj.compute_weighted_gt_metrics()
    metrics_obj.generate_pdf_output()
    graph_obj.remove_listener(print_progress)
    metrics_obj.remove_listener(print_progress)


def print_progress(x, y):
    """
    Simple method to display progress updates.

    Args:
        x (int): progress value.
        y (str): progress message.
    Returns:
         None:
    """
    print(str(x) + "%: " + y)
    logging.info(str(x) + "%: " + y, extra={'user': 'SGT Logs'})

