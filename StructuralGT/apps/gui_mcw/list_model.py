from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex

class ListModel(QAbstractListModel):
    IdRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2

    def __init__(self, images=None):
        super().__init__()
        self._images = images if images else []

    def rowCount(self, parent=QModelIndex()):
        return len(self._images)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        image = self._images[index.row()]
        if role == self.IdRole:
            return image["id"]
        elif role == self.NameRole:
            return image["name"]
        return None

    def roleNames(self):
        return {
            self.IdRole: b"id",
            self.NameRole: b"name",
        }

    def reset_data(self, images):
        self.beginResetModel()
        self._images = images
        self.endResetModel()
