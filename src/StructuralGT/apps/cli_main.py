# SPDX-License-Identifier: GNU GPL v3

"""
Terminal interface implementations
"""

import os
import sys
import logging
from optparse import OptionParser

from ..utils.sgt_utils import verify_path, AbortException
from ..utils.config_loader import strict_read_config_file
from ..imaging.image_processor import ImageProcessor, ALLOWED_IMG_EXTENSIONS
from ..compute.graph_analyzer import GraphAnalyzer

logger = logging.getLogger("SGT App")
# logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stdout)

class TerminalApp:
    """Exposes the terminal interface for StructuralGT."""

    def __init__(self, config_path: str):
        """
        Exposes methods for running StructuralGT tasks
        :param config_path: the path to the configuration file
        """
        # Create graph objects
        self.config_file = config_path
        self.allow_auto_scale = True
        self.sgt_objs = {}

    def create_sgt_object(self, img_path, out_dir):
        """
        A function that processes a selected image file and creates an analyzer object with default configurations.

        Args:
            img_path (str): file path to image
            out_dir (str): file path to the output folder.

        Returns:
        """

        success, result = verify_path(img_path)
        if success:
            img_path = result
            if out_dir != "":
                path_ok, new_path = verify_path(out_dir)
                out_dir = new_path if path_ok else ""
        else:
            logging.info(result, extra={'user': 'SGT Logs'})
            return False

        # Create an SGT object as a GraphAnalyzer object.
        try:
            ntwk_p, img_file = ImageProcessor.create_imp_object(img_path, out_dir, self.config_file, self.allow_auto_scale)
            sgt_obj = GraphAnalyzer(ntwk_p)
            self.sgt_objs[img_file] = sgt_obj
            return True
        except Exception as err:
            logging.exception("File Error: %s", err, extra={'user': 'SGT Logs'})
            return False

    def get_selected_sgt_obj(self, obj_index: int = 0):
        """
        Retrieve the SGT object at a specified index.
        Args:
            obj_index: index of the SGT object to retrieve
        """
        try:
            keys_list = list(self.sgt_objs.keys())
            key_at_index = keys_list[obj_index]
            sgt_obj = self.sgt_objs[key_at_index]
            return sgt_obj
        except IndexError:
            logging.info("No Image Error: Please import/add an image.", extra={'user': 'SGT Logs'})
            return None

    def add_single_image(self, image_path, output_dir):
        """
        Verify and validate an image path, use it to create an SGT object

        :param image_path: image path to be processed
        :param output_dir: output directory for saving output files
        :return: bool result of SGT object creation
        """
        is_created = self.create_sgt_object(image_path, output_dir)
        if not is_created:
            logging.info("Fatal Error: Unable to create SGT object", extra={'user': 'SGT Logs'})
        return is_created

    def add_multiple_images(self, img_dir_path, output_dir):
        """
        Verify and validate multiple image paths, use each to create an SGT object.
        """

        success, result = verify_path(img_dir_path)
        if success:
            img_dir_path = result
        else:
            logging.info(result, extra={'user': 'SGT Logs'})
            return False

        files = os.listdir(img_dir_path)
        files = sorted(files)
        for a_file in files:
            allowed_extensions = tuple(ext[1:] if ext.startswith('*.') else ext for ext in ALLOWED_IMG_EXTENSIONS)
            if a_file.endswith(allowed_extensions):
                img_path = os.path.join(str(img_dir_path), a_file)
                self.create_sgt_object(img_path, output_dir)

        if len(self.sgt_objs) <= 0:
            logging.info("File Error: Files have to be either .tif .png .jpg .jpeg", extra={'user': 'SGT Logs'})
            return False
        else:
            return True

    def task_extract_graph(self, selected_index: int = 0):
        """"""
        sgt_obj = self.get_selected_sgt_obj(obj_index=selected_index)
        ntwk_p = sgt_obj.ntwk_p
        try:
            ntwk_p.abort = False
            ntwk_p.add_listener(TerminalApp.update_progress)
            ntwk_p.apply_img_filters()
            ntwk_p.build_graph_network()
            ntwk_p.remove_listener(TerminalApp.update_progress)
            if ntwk_p.abort:
                raise AbortException("Process aborted")
            TerminalApp.update_progress(100, "Graph successfully extracted!")
            return ntwk_p
        except AbortException as err:
            logging.exception("Task Aborted: %s", err, extra={'user': 'SGT Logs'})
            # Clean up listeners before exiting
            ntwk_p.remove_listener(TerminalApp.update_progress)
            # Emit failure signal (aborted)
            msg = "Graph extraction aborted due to error! Change image filters and/or graph settings and try again. If error persists then close the app and try again"
            logging.info(f"Extract Graph Aborted: {msg}", extra={'user': 'SGT Logs'})
            return None

    def task_compute_gt(self, selected_index: int = 0):
        """"""
        sgt_obj = self.get_selected_sgt_obj(obj_index=selected_index)
        success, new_sgt = GraphAnalyzer.safe_run_analyzer(sgt_obj, TerminalApp.update_progress)
        if success:
            GraphAnalyzer.write_to_pdf(new_sgt, TerminalApp.update_progress)
            return new_sgt
        else:
            msg = "Either task was aborted by user or a fatal error occurred while computing GT parameters. Change image filters and/or graph settings and try again. If error persists then close the app and try again."
            logging.info(f"SGT Computations Failed: {msg}", extra={'user': 'SGT Logs'})
            return None

    def task_compute_multi_gt(self):
        """"""
        new_sgt_objs = GraphAnalyzer.safe_run_multi_analyzer(self.sgt_objs, TerminalApp.update_progress)
        if new_sgt_objs is None:
            msg = "Either task was aborted by user or a fatal error occurred while computing GT parameters. Change image filters and/or graph settings and try again. If error persists then close the app and try again."
            logging.info(f"SGT Computations Failed: {msg}", extra={'user': 'SGT Logs'})
        return new_sgt_objs

    @staticmethod
    def update_progress(progress_val, msg):
        """
        Simple method to display progress updates.

        Args:
            progress_val (int): progress value
            msg (str): progress message
        Returns:
             None:
        """

        if 0 <= progress_val <= 100:
            print(f"{progress_val} %: {msg}")
            logging.info(f"{progress_val} %: {msg}", extra={'user': 'SGT Logs'})
        elif progress_val > 100:
            print(f"{msg}")
            logging.info(f"{msg}", extra={'user': 'SGT Logs'})
        else:
            print(f"Error: {msg}")
            logging.exception(f"{msg}", extra={'user': 'SGT Logs'})

    @classmethod
    def execute(cls):
        """Initializes and starts the terminal/CMD the StructuralGT application."""

        # Retrieve user settings
        opt_parser = OptionParser()
        opt_parser.add_option('-f', '--inputFile',
                             dest='img_path',
                             help='path to image file',
                             default="",
                             type='string')
        opt_parser.add_option('-d', '--inputDir',
                             dest='img_dir_path',
                             help='path to folder containing images',
                             default="",
                             type='string')
        opt_parser.add_option('-o', '--outputDir',
                              dest='output_dir',
                              help='path to folder for saving output files. If not provided, output files will be saved in input dir.',
                              default="",
                              type='string')
        opt_parser.add_option('-s', '--allowAutoScale',
                             dest='auto_scale',
                             help='allow automatic scaling of images',
                             default=1,
                             type='int')
        opt_parser.add_option('-t', '--runTask',
                              dest='run_task',
                              help='you can run the following tasks: (1) extract graph; (2) compute GT metrics.',
                              default=2,
                              type='int')
        opt_parser.add_option('-c', '--config',
                              dest='config_file',
                              help='path to config file',
                              default="",
                              type='string')
        # opt_parser.add_option('-m', '--runMultiGT',
        #                      dest='run_multi_gt',
        #                      help='run compute GT parameters on multiple images',
        #                      default=0,
        #                      type='int')
        # opt_parser.add_option('-i', '--selectedImgIndex',
        #                      dest='sel_img_idx',
        #                      help='index of selected image',
        #                      default=0,
        #                      type='int')
        (cfg, args) = opt_parser.parse_args()
        cfg.auto_scale = bool(cfg.auto_scale)
        # cfg.run_multi_gt = bool(cfg.run_multi_gt)

        # Create Terminal App
        term_app = cls(cfg.config_file)

        # 1. Verify config file
        config_file_ok = strict_read_config_file(cfg.config_file, term_app.update_progress)
        if not config_file_ok:
            sys.exit('Usage: StructuralGT-cli -f datasets/InVitroBioFilm.png -c datasets/sgt_configs.ini -t 2 -o results/')

        # 2. Get images and process them
        if cfg.img_path != "":
            term_app.add_single_image(cfg.img_path, cfg.output_dir)
        elif cfg.img_dir_path != "":
            term_app.add_multiple_images(cfg.img_dir_path, cfg.output_dir)
        else:
            term_app.update_progress(-1, "No image path/image folder provided! System will exit.")
            sys.exit('System exit')

        # 3. Execute specific task
        if cfg.run_task == 1:
            term_app.task_extract_graph()
        elif cfg.run_task == 2:
            run_multi_gt = True if cfg.img_dir_path != "" else False
            term_app.task_compute_multi_gt() if run_multi_gt else term_app.task_compute_gt()
        else:
            term_app.update_progress(-1, "Invalid GT task selected! System will exit.")
            sys.exit('System exit')
