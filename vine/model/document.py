# ======================================================================================================================
#      File:  /vine/model/document.py
#   Project:  Vine
#    Author:  Jared Julien <jaredjulien@exsystems.net>
# Copyright:  (c) 2022 Jared Julien, eX Systems
# ---------------------------------------------------------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ----------------------------------------------------------------------------------------------------------------------
"""A document represents the root node in the tree and contains a set of articles."""

# ======================================================================================================================
# Imports
# ----------------------------------------------------------------------------------------------------------------------
import re

from PySide6 import QtCore
from markdown import markdown

from vine.model.article import Article




# ======================================================================================================================
# Document Class
# ----------------------------------------------------------------------------------------------------------------------
class Document(QtCore.QAbstractItemModel):

    dataChanged = QtCore.Signal(QtCore.QModelIndex, QtCore.QModelIndex, object)

    def __init__(self):
        super().__init__()
        self.root: Article = Article('root', '')
        self._cached = ''


# ----------------------------------------------------------------------------------------------------------------------
    def load(self, filename: str):
        """Load a document from file."""
        self.beginResetModel()

        with open(filename, 'r', encoding='utf-8') as handle:
            document = handle.read()

        self._cached = document

        # Convert underline headings to pound headings.
        document = re.sub('(.+)\n===+\n', r'# \1\n', document)
        document = re.sub('(.+)\n---+\n', r'## \1\n', document)

        # Ensure that the document ends with a newline.
        document += '\n'

        # Parse out sections using headings as titles.
        previous_level = 0
        parents = []
        child = self.root
        sections = re.split('(^#+)', document, flags=re.MULTILINE)[1:]
        for heading, content in zip(sections[::2], sections[1::2]):
            level = len(heading)
            while level > previous_level:
                parents.append(child)
                previous_level += 1
            while level < previous_level:
                parents.pop()
                previous_level -= 1
            parent = parents[-1]
            parent.insert_children(parent.child_count(), 1)
            child = parent.last_child()
            title, body = content.split('\n', 1)
            child.set_data(0, title.strip())
            child.set_data(1, body.strip())

        self.endResetModel()

        index = self.createIndex(0, 0)
        self.dataChanged.emit(index, index, [QtCore.Qt.DisplayRole])


# ----------------------------------------------------------------------------------------------------------------------
    def dump(self, filename: str) -> None:
        """Write the contents of this model to the provided filename.

        Arguments:
            filename: The path and name of the file to which the contents of this Document are to be dumped.
        """
        document = self.dumps()
        with open(filename, 'w', encoding='utf-8') as handle:
            handle.write(document)
        self._cached = document

        index = self.createIndex(0, 0)
        self.dataChanged.emit(index, index, [QtCore.Qt.DisplayRole])


# ----------------------------------------------------------------------------------------------------------------------
    def dumps(self) -> str:
        """Return the contents of this document as a sting."""
        def dump_node(root: Article, level: int = 1) -> str:
            text = ''
            for article in root.children:
                text += max(2, 7 - level) * '\n'
                text += ('#' * level) + f' {article.title}\n'
                text += article.body.rstrip('\n')
                text += dump_node(article, level + 1)
            return text

        return dump_node(self.root).strip('\n')


# ----------------------------------------------------------------------------------------------------------------------
    def dirty(self) -> bool:
        current = self.dumps()
        return current != self._cached


# ----------------------------------------------------------------------------------------------------------------------
    def to_html(self) -> str:
        text = self.dumps()
        extensions = [
            'admonition',
            'codehilite',
            'extra'
        ]
        html = markdown(text, extensions=extensions)
        return html


# ----------------------------------------------------------------------------------------------------------------------
    def clear(self):
        self.beginResetModel()
        self.root.clear()
        self._cached = ''
        self.endResetModel()


# ----------------------------------------------------------------------------------------------------------------------
    def get_item(self, index: QtCore.QModelIndex = QtCore.QModelIndex()) -> Article:
        if index.isValid():
            item: Article = index.internalPointer()
            if item:
                return item
        return self.root


# ----------------------------------------------------------------------------------------------------------------------
    def index(self, row: int, column: int, parent: QtCore.QModelIndex) -> QtCore.QModelIndex:
        if parent.isValid() and parent.column() != 0:
            return QtCore.QModelIndex()

        parent_item: Article = self.get_item(parent)
        if not parent_item:
            return QtCore.QModelIndex()

        child_item: Article = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QtCore.QModelIndex()


# ----------------------------------------------------------------------------------------------------------------------
    def parent(self, index: QtCore.QModelIndex = QtCore.QModelIndex()) -> QtCore.QModelIndex:
        if not index.isValid():
            return QtCore.QModelIndex()

        child_item: Article = self.get_item(index)
        if child_item:
            parent_item: Article = child_item.parent()
        else:
            parent_item = None

        if parent_item == self.root or not parent_item:
            return QtCore.QModelIndex()

        return self.createIndex(parent_item.child_number(), 0, parent_item)


# ----------------------------------------------------------------------------------------------------------------------
    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.DisplayRole) -> any:
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole and role != QtCore.Qt.EditRole:
            return None

        article: Article = self.get_item(index)
        return article.data(index.column())


# ----------------------------------------------------------------------------------------------------------------------
    def setData(self, index: QtCore.QModelIndex, value: any, role: int = QtCore.Qt.EditRole) -> bool:
        """Sets the role data for the item at the specified index to the provided value.

        Arguments:
            index: The location of the data being updated.
            value: The value of the data at the location and role.
            role: Specifies the role of the provided data.

        Returns:
            True when the update was successful.
        """
        if role not in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
            return False

        item: Article = self.get_item(index)
        result: bool = item.set_data(index.column(), value)

        if result:
            self.dataChanged.emit(index, index, [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole])

        return result


# ----------------------------------------------------------------------------------------------------------------------
    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        """Returns the item flags for the given index.

        Specifically this method adds ItemEditable to those provided by the base class.
        """
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        flags = super().flags(index)
        flags |= QtCore.Qt.ItemIsEditable
        flags |= QtCore.Qt.ItemIsDragEnabled
        flags |= QtCore.Qt.ItemIsDropEnabled
        return flags


# ----------------------------------------------------------------------------------------------------------------------
    def supportedDropActions(self):
        return QtCore.Qt.MoveAction


# ----------------------------------------------------------------------------------------------------------------------
    def insertRows(self, position: int, rows: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        parent_item: Article = self.get_item(parent)
        if not parent_item:
            return False

        self.beginInsertRows(parent, position, position + rows - 1)
        success: bool = parent_item.insert_children(position, rows)
        self.endInsertRows()

        return success


# ----------------------------------------------------------------------------------------------------------------------
    def removeRows(self, position: int, rows: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        parent_item: Article = self.get_item(parent)
        if not parent_item:
            return False

        self.beginRemoveRows(parent, position, position + rows - 1)
        success: bool = parent_item.remove_children(position, rows)
        self.endRemoveRows()

        return success


# ----------------------------------------------------------------------------------------------------------------------
    def rowCount(self, parent: QtCore.QModelIndex) -> int:
        if parent.isValid() and parent.column() > 0:
            return 0

        parent_item: Article = self.get_item(parent)
        if not parent_item:
            return 0
        return parent_item.child_count()


# ----------------------------------------------------------------------------------------------------------------------
    def columnCount(self, _parent: QtCore.QModelIndex) -> int:
        return 2


# ----------------------------------------------------------------------------------------------------------------------
    def _repr_recursion(self, item: Article, indent: int = 0) -> str:
        result = " " * indent + repr(item) + "\n"
        for child in item.children:
            result += self._repr_recursion(child, indent + 2)
        return result


# ----------------------------------------------------------------------------------------------------------------------
    def __repr__(self) -> str:
        return self._repr_recursion(self.root)




# End of File
