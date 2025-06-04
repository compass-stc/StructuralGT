import os
import time
import logging
from PySide6.QtCore import QObject,QThread,Signal


class QThreadWorker(QThread):
    def __init__(self, func, args, parent=None):
        super().__init__(parent)
        self.func = func  # Store function reference
        self.args = args  # Store arguments

    def run(self):
        if self.func:
            self.func(*self.args)  # Call function with arguments

class WorkerTask (QObject):
    taskFinishedSignal = Signal(bool, object) # success/fail (True/False), result (object)

    def __init__(self):
        super().__init__()

    def task_run_binarizer(self, image, options):
        try:
            image.network.binarize(options=options)
            image.binary_loaded = True
            self.taskFinishedSignal.emit(True, image)
        except Exception as err:
            logging.exception("Binarizer Error: %s", err, extra={'user': 'SGT Logs'})
            self.taskFinishedSignal.emit(False, ["Binarizer Failed", "Error applying binarizer."])
    
    def task_run_graph_extraction(self, image):
        try:
            if image.binary_loaded == False:
                self.taskFinishedSignal.emit(False, ["Graph Extraction Failed", "Please run binarizer first."])
                return
            image.network.img_to_skel()
            image.network.set_graph()
            image.graph_loaded = True
            self.taskFinishedSignal.emit(True, image)
        except Exception as err:
            logging.exception("Graph Error: %s", err, extra={'user': 'SGT Logs'})
            self.taskFinishedSignal.emit(False, ["Graph Extraction Failed", "Error extracting graph."])
