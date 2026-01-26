"""Network service for StructuralGT GUI."""

from StructuralGT.electronic import Electronic
from StructuralGT.geometric import Nematic
from StructuralGT.structural import (
    Assortativity,
    Closeness,
    Clustering,
    Degree,
    Size,
)
from model.handler import NetworkHandler, PointNetworkHandler, HandlerRegistry


class NetworkService:
    """Network service for StructuralGT GUI."""

    @staticmethod
    def add_network(handler_registry: HandlerRegistry, folder_path: str, dim: int):
        """Add a NetworkHandler to the handler registry."""
        network_handler = NetworkHandler(folder_path, dim=dim)
        handler_registry.add(network_handler)
        return

    @staticmethod
    def add_point_network(handler_registry: HandlerRegistry, file_path: str):
        """Add a PointNetworkHandler to the handler registry."""
        point_handler = PointNetworkHandler(file_path)
        handler_registry.add(point_handler)
        return

    @staticmethod
    def delete_network(handler_registry: HandlerRegistry, index: int):
        """Delete a Handler from the handler registry."""
        handler_registry.delete(index)
        return

    @staticmethod
    def binarize_selected_network(
        handler_registry: HandlerRegistry,
        options: dict,
    ):
        """Binarize the selected network."""
        handler = handler_registry.get_selected()
        if handler and isinstance(handler, NetworkHandler):
            handler["binarize_options"] = options
            handler["network"].binarize(options)
            handler["ui_properties"]["binarized_loaded"] = True
        return

    @staticmethod
    def extract_graph_from_selected_network(
        handler_registry: HandlerRegistry,
        weight_type,
    ):
        """Extract the graph from the selected network."""
        handler = handler_registry.get_selected()
        if handler and isinstance(handler, NetworkHandler):
            handler["network"].img_to_skel()
            handler["network"].set_graph()
            handler["ui_properties"]["extracted_loaded"] = True
        return

    @staticmethod
    def compute_diameter_and_density(handler_registry: HandlerRegistry):
        """Compute the diameter and density of the selected network."""
        handler = handler_registry.get_selected()
        if handler:
            size = Size()
            size.compute(handler["network"])
            return size.diameter, size.density
        return None, None

    @staticmethod
    def compute_average_clustering_coefficient(
        handler_registry: HandlerRegistry,
    ):
        """Compute the average clustering coeff. of the selected network."""
        handler = handler_registry.get_selected()
        if handler:
            clustering = Clustering()
            clustering.compute(handler["network"])
            return clustering.average_clustering_coefficient
        return None

    @staticmethod
    def compute_assortativity(handler_registry: HandlerRegistry):
        """Compute the assortativity of the selected network."""
        handler = handler_registry.get_selected()
        if handler:
            assortativity = Assortativity()
            assortativity.compute(handler["network"])
            return assortativity.assortativity
        return None

    @staticmethod
    def compute_average_closeness(handler_registry: HandlerRegistry):
        """Compute the average closeness of the selected network."""
        handler = handler_registry.get_selected()
        if handler:
            closeness = Closeness()
            closeness.compute(handler["network"])
            return closeness.average_closeness
        return None

    @staticmethod
    def compute_average_degree(handler_registry: HandlerRegistry):
        """Compute the average degree of the selected network."""
        handler = handler_registry.get_selected()
        if handler:
            degree = Degree()
            degree.compute(handler["network"])
            return degree.average_degree
        return None

    @staticmethod
    def compute_nematic_order_parameter(handler_registry: HandlerRegistry):
        """Compute the nematic order parameter of the selected network."""
        handler = handler_registry.get_selected()
        if handler:
            nematic = Nematic()
            nematic.compute(handler["network"])
            return nematic.nematic_order_parameter
        return None

    @staticmethod
    def compute_effective_resistance(handler_registry: HandlerRegistry):
        """Compute the effective resistance of the selected network."""
        return None

    @staticmethod
    def compute_graph_properties(
        handler_registry: HandlerRegistry,
        options: dict,
    ):
        """Compute the graph properties of the selected network."""
        handler = handler_registry.get_selected()
        if handler is not None:
            graph_properties = handler["network_properties"].copy()
            if options["diameter"] or options["density"]:
                diameter, density = NetworkService.compute_diameter_and_density(
                    handler_registry
                )
                if options["diameter"]:
                    graph_properties["diameter"] = diameter
                if options["density"]:
                    graph_properties["density"] = density
            if options["average_clustering_coefficient"]:
                average_clustering_coefficient = (
                    NetworkService.compute_average_clustering_coefficient(
                        handler_registry
                    )
                )
                graph_properties["average_clustering_coefficient"] = (
                    average_clustering_coefficient
                )
            if options["assortativity"]:
                assortativity = NetworkService.compute_assortativity(handler_registry)
                graph_properties["assortativity"] = assortativity
            if options["average_closeness"]:
                average_closeness = NetworkService.compute_average_closeness(
                    handler_registry
                )
                graph_properties["average_closeness"] = average_closeness
            if options["average_degree"]:
                average_degree = NetworkService.compute_average_degree(handler_registry)
                graph_properties["average_degree"] = average_degree
            if options["nematic_order_parameter"]:
                nematic_order_parameter = (
                    NetworkService.compute_nematic_order_parameter(handler_registry)
                )
                graph_properties["nematic_order_parameter"] = nematic_order_parameter
            if options["effective_resistance"]:
                effective_resistance = NetworkService.compute_effective_resistance(
                    handler_registry
                )
                graph_properties["effective_resistance"] = effective_resistance
            handler["network_properties"] = graph_properties
            return True
        return False
