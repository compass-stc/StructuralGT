import json
import logging
import os
import shutil
import sys
import tempfile
import uuid
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from ovito import scene
from ovito.gui import create_qwidget
from ovito.io import import_file
from ovito.vis import Viewport
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from StructuralGT import __version__
from .file_controller import FileController
from .image_provider import ImageProvider
from .view_controller import GraphViewController, ImageViewController
from .task_controller import TaskController
from ..utils.task import (
    BinarizeTask,
    ExtractGraphTask,
    GraphAnalysisTask,
)
from ..utils.handler import PointNetworkHandler, HandlerRegistry
from ..model.list_model import ListModel
from ..model.table_model import TableModel


class MainController(QObject):
    """Exposes a method to refresh the image in QML."""

    # Signals
    refreshImageSignal = Signal()  # noqa: N815
    imageRefreshedSignal = Signal()  # noqa: N815
    showAlertSignal = Signal(str, str)  # noqa: N815
    refreshGraphSignal = Signal()  # noqa: N815

    def __init__(self, qml_app: QApplication, qml_engine: QQmlApplicationEngine):
        super().__init__()
        self.qml_app = qml_app
        self.qml_engine = qml_engine

        self.registry = HandlerRegistry()
        self.file_ctrl = FileController(self.registry)
        self.image_view_ctrl = ImageViewController(self.registry)
        self.graph_view_ctrl = GraphViewController(
            self.registry, self.qml_app, self.qml_engine
        )
        self.task_ctrl = TaskController(self.registry)

        # Create Models
        self.imagePropsModel = TableModel([])
        self.graphPropsModel = TableModel([])
        self.networkListModel = ListModel([])

    @Slot(str, int)
    def add_network(self, path: str, dim: int):
        """Add a network for the given path and dimension."""
        handler = self.file_ctrl.create_network_handler(path, dim)
        if handler is None:
            self.showAlertSignal.emit("Network Error", "Error creating network.")
        else:
            self.registry.add(handler)
            self.registry.select(self.registry.count() - 1)
            self.refreshImageSignal.emit()

    @Slot(str, float)
    def add_point_network(self, path: str, cutoff: float):
        """Add a point network for the given path and dimension."""
        handler = self.file_ctrl.create_point_network_handler(path, cutoff)
        if handler is None:
            self.showAlertSignal.emit(
                "Point Network Error", "Error creating point network."
            )
        else:
            self.registry.add(handler)
            self.registry.select(self.registry.count() - 1)
            self.refreshGraphSignal.emit()

    @Slot()
    def refresh_image_view(self):
        """Refresh the image in the GUI."""
        try:
            self.refreshImageSignal.emit()
        except Exception as e:
            logging.exception(
                "Image Loading Error: %s", e, extra={"user": "SGT Logs"}
            )
            self.showAlertSignal.emit(
                "Image Error", "Error loading image. Try again."
            )

    @Slot(result=str)
    def get_display_info(self):
        """Get display information for the current image."""
        info = self.image_view_ctrl.get_display_info()
        return json.dumps(info)

    @Slot(str)
    def set_display_type(self, display_type: str):
        """Set the display type for the image view."""
        self.image_view_ctrl.set_display_type(display_type)
        self.refresh_image_view()

    @Slot(int)
    def set_selected_slice_index(self, index):
        """Set the selected slice index of the selected image."""
        self.image_view_ctrl.set_selected_slice_index(index)
        self.refresh_image_view()

    @Slot(QObject)
    def refresh_graph_view(self, container: QObject):
        """Refresh the graph in the GUI."""
        try:
            if not self.graph_view_ctrl.ovito_widget:
                self.graph_view_ctrl.attach_after_qml_loaded(container)
            if self.registry.get_selected() is None:
                return
            self.graph_view_ctrl.render_graph()
        except Exception as e:
            logging.exception(
                "Graph Refresh Error: %s", e, extra={"user": "SGT Logs"}
            )
            self.showAlertSignal.emit(
                "Graph Error", "Error refreshing graph. Try again."
            )

    @Slot(str)
    def submit_binarize_task(self, options: str):
        """Submit a binarization task."""
        # Assign unique ID
        id = str(uuid.uuid4())
        task = BinarizeTask(
            id=id,
            index=self.registry.get_selected_index(),
            options=json.loads(options)
        )
        self.task_ctrl.enqueue(task)

    @Slot(str)
    def submit_extract_graph_task(self, weights: str):
        """Submit a graph extraction task."""
        # Assign unique ID
        id = str(uuid.uuid4())
        task = ExtractGraphTask(
            id=id,
            index=self.registry.get_selected_index(),
            weights=weights
        )
        self.task_ctrl.enqueue(task)

    @Slot(str)
    def submit_graph_analysis_task(self, options: str):
        """Submit a graph analysis task."""
        # Assign unique ID
        id = str(uuid.uuid4())
        task = GraphAnalysisTask(
            id=id,
            index=self.registry.get_selected_index(),
            options=json.loads(options)
        )
        self.task_ctrl.enqueue(task)

    @Slot()
    def update_image_model(self):
        """Update the image properties model with the selected image's properties."""
        handler = self.registry.get_selected()

        if handler is None or isinstance(handler, PointNetworkHandler):
            self.imagePropsModel.reset_data([])
            return

        if handler.dim == 3:
            image_props = [
                ["Name", f"{handler.input_dir}"],
                ["Depth x Height x Width", f"{handler.network.image.shape[0]} x {handler.network.image.shape[1]} x {handler.network.image.shape[2]}"],
                ["Dimensions", "3D"]
            ]
        else:
            image_props = [
                ["Name", f"{handler.input_dir}"],
                ["Height x Width", f"{handler.network.image.shape[0]} x {handler.network.image.shape[1]}"],
                ["Dimensions", "2D"]
            ]

        self.imagePropsModel.reset_data(image_props)
        logging.info(f"Updated image properties model: {image_props}")


    @Slot()
    def update_graph_model(self):
        """Update the graph properties model."""
        handler = self.registry.get_selected()

        if handler is None:
            return

        if  isinstance(handler, PointNetworkHandler) or handler.graph_loaded:
            graph_props = [
                ["Edge Count", f"{handler.network.graph.ecount()}"],
                ["Node Count", f"{handler.network.graph.vcount()}"],
            ]

            for key, value in handler.properties.items():
                if value:
                    graph_props.append([key, f"{value:.5f}"])

            self.graphPropsModel.reset_data(graph_props)

    @Slot(str, result=str)
    def get_file_extensions(self, option):
        """Return the file extensions for the specified option."""
        return self.file_ctrl.file_filters(option)

    @Slot(result=str)
    def get_sgt_version(self):
        """Return the version of StructuralGT."""
        # Copyright (C) 2024, the Regents of the University of Michigan.
        return f"StructuralGT v{__version__}"

    @Slot(result=str)
    def get_about_details(self):
        """Return the about details of the application."""
        return (
            f"A software tool that allows graph theory analysis of nano-structures. This is a modified version "  # noqa: E501
            "of StructuralGT initially proposed by Drew A. Vecchio, DOI: "
            "<html><a href='https://pubs.acs.org/doi/10.1021/acsnano.1c04711'>10.1021/acsnano.1c04711</a></html><html><br/><br/></html>"
            "Contributors:<html><br/></html>"
            "1. Nicolas Kotov<html><br/></html>"
            "2. Dickson Owuor<html><br/></html>"
            "3. Alain Kadar<html><br/><br/></html>"
            "Documentation:<html><br/></html>"
            "<html><a href='https://structuralgt.readthedocs.io'>structuralgt.readthedocs.io</a></html><html><br/><br/></html>"
            f"{self.get_sgt_version()}<html><br/></html>"
            "Copyright (C) 2018-2025, The Regents of the University of Michigan.<html><br/></html>"  # noqa: E501
            "License: GPL GNU v3<html><br/></html>"
        )
