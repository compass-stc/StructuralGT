from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex


class TreeItem:
    """ Represents a single item in the tree. """
    def __init__(self, data, parent=None):
        self._data = data  # Dictionary of data (id, text, value)
        self._parent = parent
        self.children = []

    def append_child(self, child):
        """ Adds a child node to this item. """
        self.children.append(child)

    def child(self, row):
        """ Returns the child at the specified row. """
        return self.children[row] if row < len(self.children) else None

    def child_count(self):
        """ Returns the number of children. """
        return len(self.children)

    def column_count(self):
        """ Returns the number of columns (3: id, text, value). """
        return len(self._data)

    def data(self, column):
        """ Returns the data for a specific column. """
        if column == 0:
            return self._data.get("id", "")
        elif column == 1:
            return self._data.get("text", "")
        elif column == 2:
            return self._data.get("value", 0)
        return None

    def set_data(self, column, value):
        """ Sets the data for a specific column. """
        if column == 0:
            self._data["id"] = value
        elif column == 1:
            self._data["text"] = value
        elif column == 2:
            self._data["value"] = value
        return True

    def parent(self):
        """ Returns the parent of this item. """
        return self._parent

    def row(self):
        """ Returns this item's index in its parent's children list. """
        if self._parent:
            return self._parent.children.index(self)
        return 0


class TreeModel(QAbstractItemModel):
    """ QAbstractItemModel for displaying hierarchical data in QML. """
    # Qt.UserRole
    IdRole = Qt.ItemDataRole.UserRole + 1
    TextRole = Qt.ItemDataRole.UserRole + 2
    ValueRole = Qt.ItemDataRole.UserRole + 3

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._rootItem = TreeItem({"id": "root", "text": "Root", "value": None})
        self.setup_model_data(data, self._rootItem)
        # self.

    def setup_model_data(self, data_list, parent):
        """ Populates the model with data from a list of dictionaries. """
        for item_data in data_list:
            item = TreeItem(item_data, parent)
            parent.append_child(item)
            if 'items' in item_data:
                self.setup_model_data(item_data['items'], item)

    def rowCount(self, parent=QModelIndex()):
        """ Returns the children count of the given parent. """
        if not parent.isValid():
            return self._rootItem.child_count()
        return parent.internalPointer().child_count()

    def columnCount(self, parent=QModelIndex()):
        """ Returns the number of columns (fixed at 3). """
        return 1

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """ Returns the data to be displayed. """
        if not index.isValid():
            return None
        item = index.internalPointer()
        # if role == Qt.DisplayRole:
        #    return item.data(index.column())
        if role == self.IdRole:
            return item.data(0)  # id
        elif role == self.TextRole:
            return item.data(1)  # text
        elif role == self.ValueRole:
            return item.data(2)  # value
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False
        item = index.internalPointer()
        col = 2  # for valueRole
        if item.set_data(col, value):
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def reset_data(self, new_data):
        """ Resets the data to be displayed. """
        self.beginResetModel()
        self._rootItem = TreeItem({"id": "root", "text": "Root", "value": None})
        self.setup_model_data(new_data, self._rootItem)
        self.endResetModel()
        self.dataChanged.emit(self.index(0,0), self.index(len(new_data), 0),
                              [self.IdRole, self.TextRole, self.ValueRole])

    def parent(self, index=QModelIndex()):
        """ Returns the parent index of a given child index. """
        if not index.isValid():
            return QModelIndex()

        item = index.internalPointer()
        parent_item = item.parent()

        if parent_item == self._rootItem:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def index(self, row, column, parent=QModelIndex()):
        """ Returns the index of a given row and column. """
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parent_item = self._rootItem if not parent.isValid() else parent.internalPointer()
        child_item = parent_item.child(row)

        if child_item:
            return self.createIndex(row, column, child_item)

        return QModelIndex()

    def roleNames(self):
        return {
            self.IdRole: b"id",
            self.TextRole: b"text",
            self.ValueRole: b"value",
        }
