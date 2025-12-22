"""Main controller for StructuralGT GUI."""

from PySide6.QtCore import QObject, Signal, QThread
from service.ui_service import UIService
from service.network_service import NetworkService
from model.handler import HandlerRegistry, NetworkHandler, PointNetworkHandler
from model.task_list_model import Task
from typing import Optional, Callable, Any
import numpy as np
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class Worker(QThread):
    """Worker thread for StructuralGT GUI."""

    def __init__(
        self,
        func: Callable,
        callback: Optional[Callable] = None,
        task: Optional[Task] = None,
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize the worker."""
        super().__init__()
        self.func = func
        self.callback = callback
        self.task = task
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """Run the worker."""
        try:
            if self.task:
                logger.info(
                    f"Task {self.task.task_id} started at "
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )

                result = self.func(*self.args, **self.kwargs)

                if self.callback:
                    self.callback(result)
                    logger.info(
                        f"Task {self.task.task_id} completed at "
                        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
        except Exception as e:
            if self.callback:
                self.callback(None, e)


class MainController(QObject):
    """Main controller for StructuralGT GUI."""

    change_view_signal = Signal(str)
    alert_signal = Signal(str, str)
    handler_changed_signal = Signal()
    binarize_finished_signal = Signal(bool)
    extract_graph_finished_signal = Signal(str)
    compute_graph_properties_finished_signal = Signal(bool)
    task_changed_signal = Signal()

    def __init__(self, handler_registry: HandlerRegistry):
        """Initialize the main controller."""
        super().__init__()
        self.handler_registry = handler_registry
        self._active_threads = []

    # ========================= Main thread methods =========================
    def add_network(self, folder_path: str, dim: int):
        """Add a network to the handler registry."""
        try:
            NetworkService.add_network(self.handler_registry, folder_path, dim)
        except Exception as e:
            self.alert_signal.emit("Failed to add Network", repr(e))
            return
        self.handler_changed_signal.emit()
        self.change_view_signal.emit("Raw Image")
        return

    def add_point_network(self, file_path: str):
        """Add a point network to the handler registry."""
        try:
            NetworkService.add_point_network(self.handler_registry, file_path)
        except Exception as e:
            self.alert_signal.emit("Failed to add Point Network", repr(e))
            return
        self.handler_changed_signal.emit()
        pipeline = UIService.get_selected_extracted_graph(
            self.handler_registry
        )
        self.extract_graph_finished_signal.emit(pipeline)
        self.change_view_signal.emit("Extracted Graph Only")
        return

    def delete_network(self, index: int):
        """Delete a network from the handler registry."""
        try:
            NetworkService.delete_network(self.handler_registry, index)
        except Exception as e:
            self.alert_signal.emit(
                "Failed to delete Network/Point Network", repr(e)
            )
            return
        self.handler_changed_signal.emit()
        if self.handler_registry.count() == 0:
            self.change_view_signal.emit("Welcome Page")
        return

    def get_selected_handler(self):
        """Get the selected handler from the handler registry."""
        return self.handler_registry.get_selected()

    def set_selected_index(self, index: int):
        """Set the selected index of the handler registry."""
        try:
            UIService.set_selected_index(self.handler_registry, index)
        except Exception as e:
            self.alert_signal.emit("Failed to set selected index", repr(e))
            return
        self.handler_changed_signal.emit()

        # Update view based on handler type
        handler = self.handler_registry.get(index)
        if handler is not None:
            if isinstance(handler, NetworkHandler):
                self.change_view_signal.emit("Raw Image")
            elif isinstance(handler, PointNetworkHandler):
                # Get the graph pipeline for point network
                pipeline = self.get_selected_extracted_graph()
                if pipeline:
                    self.extract_graph_finished_signal.emit(pipeline)
                self.change_view_signal.emit("Extracted Graph Only")

        return

    def set_selected_slice_index(self, index: int):
        """Set the selected slice index of the selected handler."""
        try:
            UIService.set_selected_slice_index(self.handler_registry, index)
        except Exception as e:
            self.alert_signal.emit(
                "Failed to set selected slice index", repr(e)
            )
            return
        self.handler_changed_signal.emit()
        return

    def get_selected_slice_raw_image(self, index: int) -> Optional[np.ndarray]:
        """Get the selected slice raw image from the selected handler."""
        try:
            image = UIService.get_selected_slice_raw_image(
                self.handler_registry, index
            )
        except Exception as e:
            self.alert_signal.emit(
                "Failed to get selected slice raw image", repr(e)
            )
            return None
        return image

    def get_selected_slice_binarized_image(
        self, index: int
    ) -> Optional[np.ndarray]:
        """Get the selected slice binarized image from the selected handler."""
        try:
            image = UIService.get_selected_slice_binarized_image(
                self.handler_registry, index
            )
        except Exception as e:
            self.alert_signal.emit(
                "Failed to get selected slice binarized image", repr(e)
            )
            return None
        return image

    def get_selected_extracted_graph(self) -> Optional[str]:
        """Get the selected extracted graph from the selected handler."""
        try:
            pipeline = UIService.get_selected_extracted_graph(
                self.handler_registry
            )
        except Exception as e:
            self.alert_signal.emit(
                "Failed to get selected extracted graph", repr(e)
            )
            return None
        return pipeline

    # ========================= Worker thread methods =========================
    def binarize_selected_network(self, options: dict):
        """Binarize the selected network."""
        if self.handler_registry.task_count() >= 10:
            self.alert_signal.emit(
                "Task limit reached", "Maximum of 10 concurrent tasks allowed."
            )
            return

        handler = self.handler_registry.get_selected()
        if not handler or handler["tasks"]["Binarize"]:
            return

        task = Task(task_id=str(uuid.uuid4()), task_type="Binarize")
        handler["tasks"]["Binarize"] = task
        task.status = "Running"
        self.task_changed_signal.emit()
        logger.info(f"Task {task.task_id} created for binarization")

        def on_finished(result, error=None):
            """Send signals to the main thread."""
            handler["tasks"]["Binarize"] = None
            self.task_changed_signal.emit()

            if error:
                logger.error(f"Task {task.task_id} failed: {error}")
                self.alert_signal.emit(
                    "Failed to binarize network", repr(error)
                )
                self.binarize_finished_signal.emit(False)
            else:
                self.handler_changed_signal.emit()
                self.binarize_finished_signal.emit(True)

        worker = Worker(
            NetworkService.binarize_selected_network,
            callback=on_finished,
            task=task,
            handler_registry=self.handler_registry,
            options=options,
        )
        task.thread = worker
        self._active_threads.append(worker)
        worker.finished.connect(lambda: self._active_threads.remove(worker))
        worker.start()

    def extract_graph_from_selected_network(self, weight_type=None):
        """Extract the graph from the selected network."""
        if self.handler_registry.task_count() >= 10:
            self.alert_signal.emit(
                "Task limit reached", "Maximum of 10 concurrent tasks allowed."
            )
            return

        handler = self.handler_registry.get_selected()
        if not handler or handler["tasks"]["Extract Graph"]:
            return

        task = Task(task_id=str(uuid.uuid4()), task_type="Extract Graph")
        handler["tasks"]["Extract Graph"] = task
        task.status = "Running"
        self.task_changed_signal.emit()
        logger.info(f"Task {task.task_id} created for graph extraction")

        def on_finished(result, error=None):
            """Send signals to the main thread."""
            handler["tasks"]["Extract Graph"] = None
            self.task_changed_signal.emit()
            if error:
                logger.error(f"Task {task.task_id} failed: {error}")
                self.alert_signal.emit("Failed to extract graph", repr(error))
                self.extract_graph_finished_signal.emit(None)
            else:
                pipeline = self.get_selected_extracted_graph()
                self.handler_changed_signal.emit()
                self.extract_graph_finished_signal.emit(pipeline)

        worker = Worker(
            NetworkService.extract_graph_from_selected_network,
            callback=on_finished,
            handler_registry=self.handler_registry,
            weight_type=weight_type,
            task=task,
        )
        task.thread = worker
        self._active_threads.append(worker)
        worker.finished.connect(lambda: self._active_threads.remove(worker))
        worker.start()

    def compute_graph_properties_from_selected_network(self, options: dict):
        """Compute the graph properties of the selected network."""
        if self.handler_registry.task_count() >= 10:
            self.alert_signal.emit(
                "Task limit reached", "Maximum of 10 concurrent tasks allowed."
            )
            return

        handler = self.handler_registry.get_selected()
        if not handler or handler["tasks"]["Compute Graph Properties"]:
            return

        task = Task(
            task_id=str(uuid.uuid4()), task_type="Compute Graph Properties"
        )
        handler["tasks"]["Compute Graph Properties"] = task
        task.status = "Running"
        self.task_changed_signal.emit()
        logger.info(
            f"Task {task.task_id} created for graph properties computation"
        )

        def on_finished(result, error=None):
            """Send signals to the main thread."""
            handler["tasks"]["Compute Graph Properties"] = None
            self.task_changed_signal.emit()
            if error:
                logger.error(f"Task {task.task_id} failed: {error}")
                self.alert_signal.emit(
                    "Failed to compute graph properties", repr(error)
                )
                self.compute_graph_properties_finished_signal.emit(False)
            else:
                self.handler_changed_signal.emit()
                self.compute_graph_properties_finished_signal.emit(True)

        worker = Worker(
            NetworkService.compute_graph_properties,
            callback=on_finished,
            task=task,
            handler_registry=self.handler_registry,
            options=options,
        )
        task.thread = worker
        self._active_threads.append(worker)
        worker.finished.connect(lambda: self._active_threads.remove(worker))
        worker.start()

    def cancel_task(self, task_id: str):
        """Cancel a task."""
        for index in self.handler_registry.get_valid_indices():
            handler = self.handler_registry.get(index)
            if handler is None:
                continue
            tasks = handler["tasks"]
            for task_type, task in tasks.items():
                if task and task.task_id == task_id:
                    if task.status == "Running" and task.thread:
                        task.thread.terminate()
                        task.thread.wait()
                        handler["tasks"][task_type] = None
                        logger.info(
                            f"Task {task_id} cancelled at "
                            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                        self.task_changed_signal.emit()
                        return
                    elif task.status == "Pending":
                        handler["tasks"][task_type] = None
                        logger.info(
                            f"Task {task_id} cancelled at "
                            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                        self.task_changed_signal.emit()
                        return
        logger.warning(f"Task {task_id} not found for cancellation")
        return

    def cleanup_threads(self):
        """Clean up all active threads on app shutdown."""
        for thread in self._active_threads[:]:
            if thread.isRunning():
                thread.requestInterruption()
                if not thread.wait(1000):
                    thread.terminate()
                    thread.wait()
            self._active_threads.remove(thread)
