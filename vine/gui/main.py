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

from PySide6 import QtCore, QtGui, QtWidgets, QtPrintSupport

from vine.gui.base.main import Ui_MainWindow
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
        self.ui.tree.setModel(self.model)
        # self.ui.tree.hideColumn(1)

        self.ui.tree.selectionModel().selectionChanged.connect(self.selected)

        self.ui.actionNew.triggered.connect(self.new)
        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.actionSave.triggered.connect(self.save)
        self.ui.actionSave_As.triggered.connect(self.save_as)
        self.ui.actionSave_a_Copy.triggered.connect(self.save_copy)
        # self.ui.actionExit.triggered.connect(self.exit)
        # self.ui.actionCut.triggered.connect(self.cut)
        # self.ui.actionCopy.triggered.connect(self.copy)
        # self.ui.actionPaste.triggered.connect(self.paste)
        # self.ui.actionAbout.triggered.connect(self.about)
        # self.ui.actionContents.triggered.connect(self.contents)
        self.ui.actionPrint.triggered.connect(self.on_print)
        self.ui.actionPreview.triggered.connect(self.preview)
        self.ui.actionExportHtml.triggered.connect(self.export_html)
        self.ui.editor.textChanged.connect(self.body_changed)
        self.model.dataChanged.connect(self.changed)

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

            if self.model.root.children:
                model = self.ui.tree.selectionModel()
                index = self.model.createIndex(0, 0, self.model.root.children[0])
                model.select(index, QtCore.QItemSelectionModel.ClearAndSelect)


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
    def selected(self, selection: QtCore.QItemSelection) -> None:
        """User has selected a new title in the tree - load the corresponding body into the editor."""
        if len(selection) != 1:
            return
        index = selection.indexes()[0]
        self.article = self.model.get_item(index)
        self.ui.editor.blockSignals(True)
        self.ui.editor.setPlainText(self.article.body)
        self.ui.editor.blockSignals(False)
        self.ui.editor.setEnabled(True)


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
    def export_html(self):
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
    <body dir="ltr" data-md-color-scheme="slate">
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
