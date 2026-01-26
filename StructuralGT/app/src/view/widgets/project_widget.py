"""Project widget for StructuralGT GUI."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QDialog,
    QMenu,
)
from PySide6.QtCore import Qt, QSize, QPoint
from model.handler import HandlerRegistry, NetworkHandler, PointNetworkHandler
from model.handler_list_model import HandlerListModel
from service.main_controller import MainController
from view.dialogs.dimension_dialog import DimensionDialog
from view.dialogs.file_dialog import select_folder, select_file


class HandlerListItemWidget(QWidget):
    """List item widget for the HandlerListModel."""

    def __init__(self, model: HandlerListModel, index: int, parent):
        """Initialize the handler list item widget."""
        super().__init__(parent)
        self.model = model
        self.index = index

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        handler_index = model.data(model.index(index, 0), Qt.UserRole)
        if handler_index is None:
            return

        # Get handler from registry to check type
        handler = model.handler_registry.get(handler_index)
        if handler is None:
            return

        thumbnail = model.data(model.index(index, 0), Qt.DecorationRole)
        name = model.data(model.index(index, 0), Qt.DisplayRole)
        handler_type = model.data(model.index(index, 0), Qt.UserRole + 1)
        binarized_loaded = model.data(model.index(index, 0), Qt.UserRole + 2)
        graph_loaded = model.data(model.index(index, 0), Qt.UserRole + 3)

        thumbnail_label = QLabel()
        if thumbnail:
            thumbnail_label.setPixmap(thumbnail)
        else:
            thumbnail_label.setFixedSize(64, 64)
            thumbnail_label.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(thumbnail_label)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        name_label = QLabel(name or "Unknown")
        name_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(name_label)

        type_label = QLabel(f"Type: {handler_type or 'Unknown'}")
        type_label.setStyleSheet("color: #666; font-size: 10px;")
        info_layout.addWidget(type_label)

        status_layout = QHBoxLayout()
        status_layout.setSpacing(5)

        if isinstance(handler, NetworkHandler):
            binarized_label = self._create_status_label(
                binarized_loaded, "Binarized", "Not Binarized"
            )
            status_layout.addWidget(binarized_label)

        graph_label = self._create_status_label(
            graph_loaded, "Extracted", "Not Extracted"
        )
        status_layout.addWidget(graph_label)

        info_layout.addLayout(status_layout)
        layout.addLayout(info_layout, 1)

        self.setFixedHeight(80)

    def _create_status_label(
        self, is_loaded: bool, loaded_text: str, not_loaded_text: str
    ) -> QLabel:
        """Create a status label."""
        label = QLabel()
        if is_loaded:
            label.setStyleSheet(
                "background-color: #4CAF50; "
                "font-size: 10px; "
                "border-radius: 8px; "
                "padding: 2px 4px; "
            )
            label.setText(loaded_text)
        else:
            label.setStyleSheet(
                "background-color: #ff5666; "
                "font-size: 10px; "
                "border-radius: 8px; "
                "padding: 2px 4px; "
            )
            label.setText(not_loaded_text)
        return label


class ProjectWidget(QWidget):
    """Project widget for StructuralGT GUI."""

    def __init__(
        self,
        controller: MainController,
        parent,
    ):
        """Initialize the project widget."""
        super().__init__(parent)
        self.controller = controller
        self.model = HandlerListModel(controller.handler_registry)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(5, 5, 5, 5)
        button_layout.setSpacing(5)

        self.list_widget = QListWidget(self)
        self.list_widget.setStyleSheet("background-color: transparent;")
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._on_context_menu)

        self.button_network = QPushButton()
        self.button_network.setText("+ Image")
        self.button_network.clicked.connect(self._on_add_network)
        self.button_point_network = QPushButton()
        self.button_point_network.setText("+ Point Network")
        self.button_point_network.clicked.connect(self._on_add_point_network)
        button_layout.addWidget(self.button_network)
        button_layout.addWidget(self.button_point_network)
        layout.addLayout(button_layout)
        layout.addWidget(self.list_widget)

        self._populate_list()

    def _populate_list(self):
        self.list_widget.clear()
        row_count = self.model.rowCount()
        for i in range(row_count):
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 80))
            widget = HandlerListItemWidget(self.model, i, self.list_widget)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    def _on_item_clicked(self, item: QListWidgetItem):
        row = self.list_widget.row(item)
        handler_index = self.model.data(self.model.index(row, 0), Qt.UserRole)
        if handler_index is not None:
            self.controller.set_selected_index(handler_index)

    def refresh(self):
        """Refresh the project widget."""
        self.model.refresh()
        self._populate_list()

    def _on_add_network(self):
        """Handle add network button click."""
        dimension_dialog = DimensionDialog(self)
        if dimension_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        dim = dimension_dialog.get_dimension()
        if dim is None:
            return

        folder_path = select_folder(self)
        if folder_path:
            self.controller.add_network(folder_path, dim)

    def _on_add_point_network(self):
        """Handle add point network button click."""
        file_path = select_file(self, "CSV Files (*.csv);;All Files (*)")
        if file_path:
            self.controller.add_point_network(file_path)

    def _on_context_menu(self, position: QPoint):
        item = self.list_widget.itemAt(position)
        if item is None:
            return

        row = self.list_widget.row(item)
        handler_index = self.model.data(self.model.index(row, 0), Qt.UserRole)
        if handler_index is None:
            return

        menu = QMenu(self)
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self._on_delete_item(handler_index))

        menu.exec(self.list_widget.mapToGlobal(position))

    def _on_delete_item(self, handler_index: int):
        self.controller.delete_network(handler_index)
