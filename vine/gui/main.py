# ======================================================================================================================
#      File:  /vine/gui/main.py
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
"""Main Window GUI."""

# ======================================================================================================================
# Imports
# ----------------------------------------------------------------------------------------------------------------------
import importlib.metadata
import os
from typing import List

from PySide6 import QtCore, QtGui, QtWidgets, QtPrintSupport

from vine.gui.base.main import Ui_MainWindow
from vine.model.article import Article
from vine.model.document import Document




# ======================================================================================================================
# Main Window Class
# ----------------------------------------------------------------------------------------------------------------------
class MainWindow(QtWidgets.QMainWindow):
    """Extends the generated Qt MainWindow UI to add functionality for the main tool window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.filename = None
        self.article = None

        self.model = Document()
        self.ui.tree.selectionModel().selectionChanged.connect(self.selected)

        self.ui.popmenu = QtWidgets.QMenu(self)
        self.ui.popmenu_insert = QtGui.QAction('Insert', self)
        self.ui.popmenu.addAction(self.ui.popmenu_insert)
        self.ui.popmenu_delete = QtGui.QAction('Delete', self)
        self.ui.popmenu_delete.setEnabled(False)
        self.ui.popmenu.addAction(self.ui.popmenu_delete)
        self.ui.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.tree.customContextMenuRequested.connect(self.context)

        self.ui.actionNew.triggered.connect(self.new)
        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.actionSave.triggered.connect(self.save)
        self.ui.actionSave_As.triggered.connect(self.save_as)
        self.ui.actionSave_a_Copy.triggered.connect(self.save_copy)
        self.ui.actionExit.triggered.connect(self.close)
        # self.ui.actionCut.triggered.connect(self.cut)
        # self.ui.actionCopy.triggered.connect(self.copy)
        # self.ui.actionPaste.triggered.connect(self.paste)
        self.ui.actionInsert.triggered.connect(self.insert)
        self.ui.actionDelete.triggered.connect(self.delete)
        self.ui.actionAbout.triggered.connect(self.about)
        self.ui.actionPrint.triggered.connect(self.on_print)
        self.ui.actionPreview.triggered.connect(self.preview)
        self.ui.actionExportHtmlWhite.triggered.connect(lambda: self.export_html('white'))
        self.ui.actionExportHtmlSlate.triggered.connect(lambda: self.export_html('slate'))
        self.ui.editor.textChanged.connect(self.body_changed)
        self.ui.tree.dropEvent = self.dropped
        self.ui.tree.itemChanged.connect(self.title_changed)
        self.ui.popmenu_insert.triggered.connect(self.insert)
        self.ui.popmenu_delete.triggered.connect(self.delete)
        self.changed()


# ----------------------------------------------------------------------------------------------------------------------
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if self.warn():
            event.accept()
        else:
            event.ignore()


# ----------------------------------------------------------------------------------------------------------------------
    def warn(self) -> bool:
        """Warn the user that there are unsaved changes and prompt them to save before continuing.

        Returns:
            True if the user has acknowledged the unsaved changes and processing should continue of False if the user
            has cancelled and the caller should cease what it was doing.
        """
        # No unsaved changes, nothing to warn about.
        if not self.model.dirty():
            return True

        # Changes exist, lets prompt the user for an action.
        flags = QtWidgets.QMessageBox.Discard
        flags |= QtWidgets.QMessageBox.Save
        flags |= QtWidgets.QMessageBox.Cancel
        message = 'What would you like to do with your unsaved changes?'
        result = QtWidgets.QMessageBox.critical(self, 'Unsaved changes', message, flags)

        # If they sad "save" then lets try to save them.
        if result == QtWidgets.QMessageBox.Save:
            return self.save()

        # It they said discard then return True indicating the software should proceed anyways.
        return result == QtWidgets.QMessageBox.Discard


# ----------------------------------------------------------------------------------------------------------------------
    def new(self):
        """Create a new, empty document for editing."""
        if self.warn():
            self.filename = None
            self.model.clear()
            self.article = None
            self.ui.tree.clear()
            self.ui.editor.clear()
            self.ui.editor.setEnabled(False)
            return True
        return False


# ----------------------------------------------------------------------------------------------------------------------
    def open(self):
        """Launch an open file dialog and select a new document to open."""
        if not self.new():
            return

        filters = [
            'Markdown (*.md *.mkd *.mdwn *.mdown *.markdown *.mdtxt *.mdtext *.workbook)',
            'XML (*.xml)'
        ]
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, filter=';;'.join(filters))
        if filename:
            self.filename = filename
            self.model.load(self.filename)
            self._render_tree()
            self.ui.tree.setSelection(QtCore.QRect(0, 0, 1, 1), QtCore.QItemSelectionModel.ClearAndSelect)
            self.ui.tree.expandAll()


# ----------------------------------------------------------------------------------------------------------------------
    def _make_item(self, article: Article) -> QtWidgets.QTreeWidgetItem:
        item = QtWidgets.QTreeWidgetItem()
        item.setText(0, article.title)
        item.setData(0, QtCore.Qt.UserRole, article)
        flags = item.flags()
        flags |= QtCore.Qt.ItemIsEditable
        item.setFlags(flags)
        return item


# ----------------------------------------------------------------------------------------------------------------------
    def _render_tree(self):
        """Helper to re-render the article tree whenever the model changes."""
        def add_node(article: Article) -> List[QtWidgets.QTreeWidgetItem]:
            roots = []
            for child in article.children:
                item = self._make_item(child)
                item.addChildren(add_node(child))
                roots.append(item)
            return roots

        roots = add_node(self.model.root)
        self.ui.tree.clear()
        self.ui.tree.addTopLevelItems(roots)
        self.changed()


# ----------------------------------------------------------------------------------------------------------------------
    def save(self) -> bool:
        """Called to save a currently open document to the opened filename.

        If no filename is set because this is a new document then revert to a "save as".

        Returns:
            Boolean True when the document is saved or False if the user cancelled out of the "save as" dialog.
        """
        if not self.filename:
            # If save was selected but this is a new document and filename hasn't been set then we need to pick a
            # filename now.
            return self.save_as()

        self.model.dump(self.filename)
        self.changed()
        return True


# ----------------------------------------------------------------------------------------------------------------------
    def _save_dialog(self):
        """Launch a save file dialog and return the selected filename.

        Shared for save as and save a copy.
        """
        filters = [
            'Markdown (*.md *.mkd *.mdwn *.mdown *.markdown *.mdtxt *.mdtext *.workbook)',
            'XML (*.xml)'
        ]
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, filter=';;'.join(filters))
        return filename


# ----------------------------------------------------------------------------------------------------------------------
    def save_as(self) -> bool:
        """Set a new filename for the document and save the contents into that.

        Returns:
            Boolean True when the document is saved or False if the user cancelled out of the "save as" dialog.
        """
        filename = self._save_dialog()
        if filename:
            self.filename = filename
            return self.save()
        return False


# ----------------------------------------------------------------------------------------------------------------------
    def save_copy(self):
        """Save a copy of the current document and continue editing under the existing filename."""
        filename = self._save_dialog()
        if filename:
            self.model.dump(self.filename)


# ----------------------------------------------------------------------------------------------------------------------
    def about(self):
        title = 'About Vine Markdown Editor'
        description = importlib.metadata.metadata('vine')['Summary'] + '\n\n'
        description += 'Author: ' + importlib.metadata.metadata('vine')['Author']
        description += ' <' + importlib.metadata.metadata('vine')['Author-email'] + '>\n'
        description += 'Copyright: (c) 2022 ' + importlib.metadata.metadata('vine')['Author']
        QtWidgets.QMessageBox.about(self, title, description)


# ----------------------------------------------------------------------------------------------------------------------
    def selected(self, selection: QtCore.QItemSelection) -> None:
        """User has selected a new title in the tree - load the corresponding body into the editor."""
        if len(selection) != 1:
            self.ui.popmenu_delete.setEnabled(False)
            self.ui.actionDelete.setEnabled(False)
            return
        self.ui.popmenu_delete.setEnabled(True)
        self.ui.actionDelete.setEnabled(True)
        index = selection.indexes()[0]
        self.article = index.data(QtCore.Qt.UserRole)
        self.ui.editor.blockSignals(True)
        self.ui.editor.setPlainText(self.article.body)
        self.ui.editor.blockSignals(False)
        self.ui.editor.setEnabled(True)


# ----------------------------------------------------------------------------------------------------------------------
    def title_changed(self, item: QtWidgets.QTreeWidgetItem) -> None:
        article = item.data(0, QtCore.Qt.UserRole)
        article.title = item.text(0)


# ----------------------------------------------------------------------------------------------------------------------
    def body_changed(self) -> None:
        """The user has modified the text in the editor window."""
        if self.article:
            self.article.body = self.ui.editor.toPlainText()
        self.changed()


# ----------------------------------------------------------------------------------------------------------------------
    def changed(self):
        """The document has changed - Update the window title to reflect the current state."""
        dirty = '*' if self.model.dirty() else ''
        filename = os.path.basename(self.filename) if self.filename else 'Untitled'
        version = importlib.metadata.version('vine')
        self.setWindowTitle(f'{dirty}{filename} - Vine Markdown Editor {version}')


# ----------------------------------------------------------------------------------------------------------------------
    def dropped(self, event):
        """Called when an article in the tree is "dropped" from a resort event.

        Because the QTreeViewWidget does not automatically handle sorting updates for use we must hook this event and
        extract the new tree structure from the UI upon a drop.
        """
        # Invoke the original parent function we are overriding.
        QtWidgets.QTreeWidget.dropEvent(self.ui.tree, event)

        def recurse(item: QtWidgets.QTreeWidgetItem) -> List[Article]:
            articles = []
            for idx in range(item.childCount()):
                child = item.child(idx)
                article = child.data(0, QtCore.Qt.UserRole)
                article.children = recurse(child)
                articles.append(article)
            return articles

        # Reload the document structure from the tree.
        self.model.root.children = []
        for idx in range(self.ui.tree.topLevelItemCount()):
            item = self.ui.tree.topLevelItem(idx)
            article = item.data(0, QtCore.Qt.UserRole)
            article.children = recurse(item)
            self.model.root.children.append(article)


# ----------------------------------------------------------------------------------------------------------------------
    def context(self, point: QtCore.QPoint):
        self.ui.popmenu.exec(self.ui.tree.mapToGlobal(point))


# ----------------------------------------------------------------------------------------------------------------------
    def insert(self):
        selection = self.ui.tree.selectedItems()
        new_article = Article('', '')
        new_item = self._make_item(new_article)
        if not selection:
            new_article.parent = self.model.root
            self.model.root.children.append(new_article)
            self.ui.tree.addTopLevelItem(new_item)
        else:
            selected_item = selection[-1]
            selected_article: Article = selected_item.data(0, QtCore.Qt.UserRole)
            new_article.parent = selected_article
            selected_article.children.append(new_article)
            selected_item.addChild(new_item)
            selected_item.setExpanded(True)
        self.ui.tree.editItem(new_item, column=0)
        self.ui.tree.clearSelection()
        new_item.setSelected(True)


# ----------------------------------------------------------------------------------------------------------------------
    def delete(self):
        selection = self.ui.tree.selectedItems()
        for item in selection:
            article: Article = item.data(0, QtCore.Qt.UserRole)
            article.parent.children.pop(article.sibling_number())
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                self.ui.tree.takeTopLevelItem(self.ui.tree.indexOfTopLevelItem(item))
        self.ui.tree.clearSelection()


# ----------------------------------------------------------------------------------------------------------------------
    def on_print(self):
        """Print the current document."""
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            browser = QtWidgets.QTextEdit()
            browser.setHtml(self.model.to_html())
            browser.print_(dialog.printer())

# ----------------------------------------------------------------------------------------------------------------------
    def preview(self):
        """Preview the HTML before printing."""
        browser = QtWidgets.QTextEdit()
        browser.setHtml(self.model.to_html())
        dialog = QtPrintSupport.QPrintPreviewDialog()
        dialog.paintRequested.connect(browser.print_)
        dialog.exec()


# ----------------------------------------------------------------------------------------------------------------------
    def export_html(self, theme: str):
        """Export the current contents of the document to an HTML file."""
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Export HTML', filter='HTML (*.html *.htm)')
        if filename:
            assets = os.path.join(os.path.dirname(__file__), '..', 'assets')
            def style(filename):
                with open(os.path.join(assets, 'css', filename), 'r', encoding='utf-8') as handle:
                    return f'<style type="text/css">{handle.read()}</style>'
            def script(filename):
                with open(os.path.join(assets, 'js', filename), 'r', encoding='utf-8') as handle:
                    return f'<script types="text/javascript">{handle.read()}</script>'
            document = self.model.to_html()
            html = f"""<html>
    <head>
        {style('main.min.css')}
        {style('palette.min.css')}
        {script('palette.min.js')}
    </head>
    <body dir="ltr" data-md-color-scheme="{theme}">
        <div class="md-container">
            <main class="md-main">
                <div class="md-main__inner md-grid">
                    <div class="md-content">
                        <article class="md-content__inner md-typeset">
                           {document}
                        </article>
                    </div>
                </div>
            </main>
        </div>
    </body>
</html>"""

            with open(filename, 'w', encoding='utf-8') as handle:
                handle.write(html)




# End of File
