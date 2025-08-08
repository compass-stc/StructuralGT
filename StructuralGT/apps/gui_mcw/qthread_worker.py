import os
import time
import logging
from PySide6.QtCore import QObject,QThread,Signal
from StructuralGT.structural import (
    Size,
    Clustering,
    Assortativity,
    Closeness,
    Degree,
)
from StructuralGT.geometric import Nematic
from StructuralGT.electronic import Electronic


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

    def task_run_binarizer(self, image):
        try:
            image.network.binarize(options=image.options)
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

    def task_run_graph_analysis(self, image, options):
        try:
            if image.graph_loaded == False:
                self.taskFinishedSignal.emit(False, ["Graph Analysis Failed", "Please run graph extraction first."])
                return
            
            print("Computing graph properties...")
            print("Options: ", options)

            network = image.network

            # Compute structural properties
            if options["Diameter"] or options["Density"]:
                size_obj = Size()
                size_obj.compute(network)
                image.properties["Diameter"] = size_obj.diameter
                image.properties["Density"] = size_obj.density

            if options["Average Clustering Coefficient"]: 
                clustering_obj = Clustering()
                clustering_obj.compute(network)
                image.properties["Average Clustering Coefficient"] = clustering_obj.average_clustering_coefficient

            if options["Assortativity"]:
                assortativity_obj = Assortativity()
                assortativity_obj.compute(network)
                image.properties["Assortativity"] = assortativity_obj.assortativity

            if options["Average Closeness"]:
                closeness_obj = Closeness()
                closeness_obj.compute(network)
                image.properties["Average Closeness"] = closeness_obj.average_closeness

            if options["Average Degree"]:
                degree_obj = Degree()
                degree_obj.compute(network)
                image.properties["Average Degree"] = degree_obj.average_degree
        
            # Compute geometric properties
            if options["Nematic Order Parameter"]:
                nematic_obj = Nematic()
                nematic_obj.compute(network)
                image.properties["Nematic Order Parameter"] = nematic_obj.nematic_order_parameter

            # Compute electronic properties
            if options["Effective Resistance"]:
                params = options["Effective Resistance"]

                required_keys = ["x0", "x1", "y0", "y1", "R_j"]
                if image.is_3d:
                    required_keys += ["z0", "z1"]

                for key in required_keys:
                    if key not in params or params[key] == "":
                        raise ValueError(f"Parameter '{key}' is required and cannot be empty.")
                    try:
                        params[key] = float(params[key])
                    except ValueError:
                        raise ValueError(f"Parameter '{key}' must be a number.")

                # TODO: Add validation for boundary conditions, e.g. 0 < x0 < x1 < width, etc.
                boundary_conditions = [
                    [params["x0"], params["x1"]],
                    [params["y0"], params["y1"]]
                ]
                if image.is_3d:
                    boundary_conditions.append([params["z0"], params["z1"]])
                    
                # TODO: Add validation for R_j and axis
                R_j = params["R_j"]
                axis = params["axis"]

                electronic_obj = Electronic()
                electronic_obj.compute(network, R_j=R_j, axis=axis, boundary_conditions=boundary_conditions)

                image.properties["Effective Resistance"] = electronic_obj.effective_resistance

            self.taskFinishedSignal.emit(True, image)
        except Exception as err:
            logging.exception("Graph Analysis Error: %s", err, extra={'user': 'SGT Logs'})
            self.taskFinishedSignal.emit(False, ["Graph Analysis Failed", "Error analyzing graph."])

    def task_process_csv(self, csv_handler):
        """Process CSV data and create graph structure."""
        try:
            # Generate graph from point network
            csv_handler.point_network.point_to_skel()
            csv_handler.graph_loaded = True
            self.taskFinishedSignal.emit(True, csv_handler)
        except Exception as e:
            self.taskFinishedSignal.emit(False, ("CSV Processing Error", str(e)))