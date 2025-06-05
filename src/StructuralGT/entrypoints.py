# SPDX-License-Identifier: GNU GPL v3

"""
Entry points that allow users to execute GUI or Cli programs
"""

import sys
import time
import logging
from .apps.gui_main import pyside_app
from .apps.cli_main import TerminalApp


logger = logging.getLogger("SGT App")
# FORMAT = '%(asctime)s; %(user)s. %(levelname)s: %(message)s'
FORMAT = '%(asctime)s; %(levelname)s: %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def main_gui():
    """
    Start the graphical user interface application.
    :return:
    """
    # Initialize log collection
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stdout)
    logging.info("SGT application started running...", extra={'user': 'SGT Logs'})

    # Install CuPy for GPU
    # detect_cuda_and_install_cupy()

    # Start GUI app
    pyside_app()

    # Log to show the App stopped
    logging.info("SGT application stopped running.", extra={'user': 'SGT Logs'})


def main_cli():
    """
    Start the terminal/CMD application.
    :return:
    """
    f_name = str('sgt_app' + str(time.time()).replace('.', '', 1) + '.log')
    logging.basicConfig(filename=f_name, encoding='utf-8', level=logging.INFO, format=FORMAT, datefmt=DATE_FORMAT)
    logging.info("SGT application started running...", extra={'user': 'SGT Logs'})

    TerminalApp.execute()
    logging.info("SGT application stopped running.", extra={'user': 'SGT Logs'})