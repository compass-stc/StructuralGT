"""Task list model for StructuralGT GUI."""

import threading
import time
from pathlib import Path
from typing import Optional, Any, List
from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Signal, QThread
from model.handler import (
    HandlerRegistry,
    Handler,
    NetworkHandler,
    PointNetworkHandler,
)


class Task:
    """Task for StructuralGT GUI."""

    def __init__(
        self,
        task_id: str,
        task_type: str,
    ):
        """Initialize the task."""
        self.task_id = task_id
        self.task_type = task_type
        self.status = "Pending"  # "Pending", "Running"
        self.thread: Optional[QThread] = None


class TaskListModel(QAbstractListModel):
    """Task list model for StructuralGT GUI."""

    data_changed_signal = Signal(QModelIndex, QModelIndex)

    def __init__(self, handler_registry: HandlerRegistry):
        """Initialize the task list model."""
        super().__init__()
        self.handler_registry = handler_registry

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows in the model."""
        if parent.isValid():
            return 0
        return len(self._get_handlers_with_tasks())

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """Return the data for the given index and role."""
        if not index.isValid():
            return None

        handlers_with_tasks = self._get_handlers_with_tasks()
        if index.row() >= len(handlers_with_tasks):
            return None

        handler = handlers_with_tasks[index.row()]
        if handler is None:
            return None

        if role == Qt.DisplayRole:
            return self._get_display_name(handler)
        elif role == Qt.UserRole:
            # Return handler_index for reference
            for idx in self.handler_registry.get_valid_indices():
                if self.handler_registry.get(idx) == handler:
                    return idx
            return None
        elif role == Qt.UserRole + 1:
            return self._get_handler_type(handler)
        elif role == Qt.UserRole + 2:
            return self._get_tasks_info(handler)
        return None

    def refresh(self):
        """Refresh the model."""
        self.beginResetModel()
        self.endResetModel()

    def _get_handlers_with_tasks(self) -> List[Handler]:
        """Get the handlers with tasks."""
        handlers_with_tasks = []
        for handler in self.handler_registry.get_all():
            if handler is not None:
                tasks = handler["tasks"]
                if any(task is not None for task in tasks.values()):
                    handlers_with_tasks.append(handler)
        return handlers_with_tasks

    def _get_display_name(self, handler: Handler) -> str:
        """Get the display name for the given handler."""
        input_dir = handler["paths"]["input_dir"]
        if input_dir:
            return Path(input_dir).name
        return "Unknown"

    def _get_handler_type(self, handler: Handler) -> str:
        """Get the handler type for the given handler."""
        ui_props = handler["ui_properties"]
        dim = ui_props.get("dim")
        if dim is None:
            return "Unknown"

        if isinstance(handler, NetworkHandler):
            return f"{dim}D Network"
        elif isinstance(handler, PointNetworkHandler):
            return "Point Network"
        return "Unknown"

    def _get_tasks_info(self, handler: Handler) -> list[dict]:
        """Get the tasks for the given handler."""
        tasks = handler["tasks"]
        tasks_info_list = []
        for task_type, task in tasks.items():
            if task is not None:
                tasks_info_list.append(
                    {
                        "task_type": task_type,
                        "task_id": task.task_id,
                        "status": task.status,
                        "task_object": task,
                    }
                )
        return tasks_info_list
