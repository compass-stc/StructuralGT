import logging
from dataclasses import dataclass

from PySide6.QtCore import QObject, QThread, Signal

from StructuralGT.electronic import Electronic
from StructuralGT.geometric import Nematic
from StructuralGT.structural import (
    Assortativity,
    Closeness,
    Clustering,
    Degree,
    Size,
)

from apps.utils import HandlerRegistry, PointNetworkHandler


@dataclass
class Task:
    """Base class for all tasks."""

    id: str  # Unique identifier for the task
    index: int  # Index of the handler
    type: str  # Type of the task

    def run(self, registry: HandlerRegistry) -> bool:
        """Run the task."""
        raise NotImplementedError("Subclasses should implement this method.")

class BinarizeTask(Task):
    """Task to binarize an image."""

    def __init__(self, id: str, index: int, options: dict):
        super().__init__(id=id, index=index, type="binarize")
        self.options = options

    def run(self, registry: HandlerRegistry) -> bool:
        """Run the binarization task."""
        handler = registry.get(self.index)
        if not handler:
            logging.error(f"Handler with index {self.index} not found.")
            return False
        if isinstance(handler, PointNetworkHandler):
            logging.error("Binarization not applicable for PointNetworkHandler.")
            return False
        try:
            handler.options = self.options
            handler.network.binarize(options=self.options)
            handler.binary_loaded = True
            return True
        except Exception as e:
            logging.exception(f"Error occurred while running binarization: {e}")
            return False

class ExtractGraphTask(Task):
    """Task to extract a graph from an image."""

    def __init__(self, id: str, index: int, weights: str):
        super().__init__(id=id, index=index, type="extract_graph")
        self.weights = weights

    def run(self, registry: HandlerRegistry) -> bool:
        """Run the graph extraction task."""
        handler = registry.get(self.index)
        if not handler:
            logging.error(f"Handler with index {self.index} not found.")
            return False
        if isinstance(handler, PointNetworkHandler):
            logging.error("Graph extraction not applicable for PointNetworkHandler.")
            return False
        try:
            handler.network.img_to_skel()
            weight_type = None if (
                not self.weights or self.weights.strip() == ""
            ) else self.weights.strip()
            handler.network.set_graph(weight_type=weight_type, write="network.gsd")
            handler.graph_loaded = True
            if hasattr(handler.network, 'Gr') and handler.network.Gr:
                handler.properties["Node Count"] = handler.network.Gr.vcount()
                handler.properties["Edge Count"] = handler.network.Gr.ecount()
            handler.graph_loaded = True
            return True
        except Exception as e:
            logging.exception(f"Error occurred while extracting graph: {e}")
            return False

class GraphAnalysisTask(Task):
    """Task to analyze the properties of a graph."""

    def __init__(self, id: str, index: int, options: dict):
        super().__init__(id=id, index=index, type="graph_analysis")
        self.options = options

    def run(self, registry: HandlerRegistry) -> bool:
        """Run the graph analysis task."""
        handler = registry.get(self.index)
        if not handler:
            logging.error(f"Handler with index {self.index} not found.")
            return False
        try:
            if self.options["Diameter"] or self.options["Density"]:
                size_obj = Size()
                size_obj.compute(handler.network)
                handler.properties["Diameter"] = size_obj.diameter
                handler.properties["Density"] = size_obj.density
            if self.options["Average Clustering Coefficient"]:
                clustering_obj = Clustering()
                clustering_obj.compute(handler.network)
                handler.properties["Average Clustering Coefficient"] = \
                    clustering_obj.average_clustering_coefficient
            if self.options["Assortativity"]:
                assortativity_obj = Assortativity()
                assortativity_obj.compute(handler.network)
                handler.properties["Assortativity"] = assortativity_obj.assortativity
            if self.options["Average Closeness"]:
                closeness_obj = Closeness()
                closeness_obj.compute(handler.network)
                handler.properties["Average Closeness"] = \
                    closeness_obj.average_closeness
            if self.options["Average Degree"]:
                degree_obj = Degree()
                degree_obj.compute(handler.network)
                handler.properties["Average Degree"] = \
                    degree_obj.average_degree
            if self.options["Nematic Order Parameter"]:
                nematic_obj = Nematic()
                nematic_obj.compute(handler.network)
                handler.properties["Nematic Order Parameter"] = \
                    nematic_obj.nematic_order_parameter
            # # TODO: implement this later
            # if self.options["Effective Resistance"]:
            #     pass
            return True
        except Exception as e:
            logging.error(f"Error occurred while analyzing graph: {e}")
            return False
