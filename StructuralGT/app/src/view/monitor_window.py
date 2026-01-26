"""Monitor window for StructuralGT GUI."""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from service.main_controller import MainController
from model.task_list_model import TaskListModel
from typing import Optional, Dict, Any, List


class TaskListItemWidget(QWidget):
    """List item widget for displaying task information."""

    def __init__(
        self,
        handler_name: str,
        handler_type: str,
        tasks_info: List[Dict[str, Any]],
        controller: MainController,
        parent,
    ):
        """Initialize the task list item widget."""
        super().__init__(parent)
        self.controller = controller
        self.handler_name = handler_name
        self.handler_type = handler_type
        self.tasks_info = tasks_info
        self.setStyleSheet("background-color: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Handler name and type
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        handler_name_label = QLabel(handler_name or "Unknown", self)
        handler_name_label.setStyleSheet("font-weight: bold; font-size: 12px;")

        handler_type_label = QLabel(handler_type or "Unknown", self)
        handler_type_label.setStyleSheet("font-size: 11px; color: #666;")
        header_layout.addWidget(handler_name_label)
        header_layout.addWidget(handler_type_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Tasks
        for task_info in tasks_info:
            task_layout = self._create_task_layout(task_info)
            layout.addLayout(task_layout)

        self.setMinimumHeight(80 + len(tasks_info) * 50)

    def _create_task_layout(self, task_info: Dict[str, Any]) -> QHBoxLayout:
        """Create the layout for a task."""
        task_layout = QHBoxLayout()
        task_layout.setContentsMargins(0, 0, 0, 0)
        task_layout.setSpacing(5)

        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        task_type_label = QLabel(task_info["task_type"] or "Unknown", self)
        task_type_label.setStyleSheet("font-weight: bold; font-size: 10px;")
        info_layout.addWidget(task_type_label)

        task_id_label = QLabel(f"ID {task_info['task_id']}", self)
        task_id_label.setStyleSheet("font-size: 9px; color: #666;")
        info_layout.addWidget(task_id_label)

        status_label = QLabel(f"Status: {task_info['status']}", self)
        status_label.setStyleSheet("font-size: 9px; color: #666;")
        info_layout.addWidget(status_label)

        task_layout.addLayout(info_layout)

        # Progress bar
        progress_bar = QProgressBar(self)
        progress_bar.setFixedHeight(12)
        progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        progress_bar.setTextVisible(False)  # Hide text for cleaner look

        if task_info["status"] == "Running":
            progress_bar.setMinimum(0)
            progress_bar.setMaximum(0)
            progress_bar.setStyleSheet(
                "QProgressBar {"
                "border: 1px solid #4CAF50;"
                "border-radius: 6px;"
                "background-color: #E8F5E9;"
                "}"
                "QProgressBar::chunk {"
                "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                "stop:0 #81C784, stop:1 #66BB6A);"
                "border-radius: 5px;"
                "}"
            )
        elif task_info["status"] == "Pending":
            progress_bar.setMinimum(0)
            progress_bar.setMaximum(100)
            progress_bar.setValue(0)
            progress_bar.setStyleSheet(
                "QProgressBar {"
                "border: 1px solid #ccc;"
                "border-radius: 6px;"
                "background-color: #f5f5f5;"
                "}"
                "QProgressBar::chunk {"
                "background-color: #E0E0E0;"
                "border-radius: 5px;"
                "}"
            )

        task_layout.addWidget(progress_bar, 1)

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedSize(60, 24)
        cancel_button.setStyleSheet(
            "QPushButton {"
            "background-color: #f44336;"
            "color: white;"
            "border: none;"
            "border-radius: 4px;"
            "font-size: 10px;"
            "}"
            "QPushButton:hover {"
            "background-color: #d32f2f;"
            "}"
            "QPushButton:pressed {"
            "background-color: #b71c1c;"
            "}"
        )
        cancel_button.clicked.connect(
            lambda: self._on_cancel_clicked(task_info["task_id"])
        )
        task_layout.addWidget(cancel_button)

        return task_layout

    def _on_cancel_clicked(self, task_id: str):
        """Handle the cancel button click."""
        self.controller.cancel_task(task_id)


class MonitorWindow(QMainWindow):
    """Monitor window for StructuralGT GUI."""

    def __init__(self, controller: MainController, parent):
        """Initialize the monitor window."""
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Task Monitor")
        self.setGeometry(200, 200, 800, 500)
        self.setMinimumSize(700, 400)

        # Central Widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Task list
        self.task_list = QListWidget(self)
        self.task_list.setSpacing(5)
        main_layout.addWidget(self.task_list, 1)

        # Task model
        self.task_model = TaskListModel(controller.handler_registry)

        # Connect task changed signal
        self.controller.task_changed_signal.connect(self.refresh)

        # Refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(2000)

        # Initial refresh
        self.refresh()

    def refresh(self):
        """Refresh the task list."""
        # Refresh model first
        self.task_model.refresh()

        self.task_list.clear()

        # Get all handlers with tasks
        row_count = self.task_model.rowCount()
        for row in range(row_count):
            index = self.task_model.index(row, 0)
            if not index.isValid():
                continue

            handler_name = self.task_model.data(index, Qt.DisplayRole)
            handler_type = self.task_model.data(index, Qt.UserRole + 1)
            tasks_info = self.task_model.data(index, Qt.UserRole + 2)

            if not handler_name or not tasks_info:  # Skip if no data
                continue

            # Create list item
            list_item = QListWidgetItem(self.task_list)
            list_item.setSizeHint(QSize(0, 80 + len(tasks_info) * 50))

            # Create custom widget
            task_widget = TaskListItemWidget(
                handler_name=handler_name,
                handler_type=handler_type or "Unknown",
                tasks_info=tasks_info,
                controller=self.controller,
                parent=self.task_list,
            )

            self.task_list.setItemWidget(list_item, task_widget)

    def closeEvent(self, event):
        """Handle close event."""
        self.refresh_timer.stop()
        super().closeEvent(event)
