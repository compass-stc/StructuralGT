"""Table models for StructuralGT GUI."""

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from typing import Any, List


class TableModel(QAbstractTableModel):
    """Table model for displaying properties in a table view."""

    def __init__(self, data=None, parent=None):
        """Initialize the table model."""
        super().__init__(parent)
        self._data = data if data is not None else []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows in the table."""
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns in the table."""
        if parent.isValid():
            return 0
        return 2 if self._data else 0

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """Return the data for the given index and role."""
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            if 0 <= row < len(self._data) and 0 <= col < len(self._data[row]):
                return self._data[row][col]

        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.DisplayRole,
    ) -> Any:
        """Return the header data for the given section and orientation."""
        return None

    def setData(self, data: List[List[Any]]) -> bool:
        """Set the data for the table."""
        self.beginResetModel()
        self._data = data
        self.endResetModel()
        return True
