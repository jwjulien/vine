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

from PySide6 import QtCore, QtGui, QtWidgets

from vine.gui.base.main import Ui_MainWindow
from vine.gui.tab import TabWidget
from vine.settings import HeadingFormat, Settings




# ======================================================================================================================
# Main Window Class
# ----------------------------------------------------------------------------------------------------------------------
class MainWindow(QtWidgets.QMainWindow):
    """Extends the generated Qt MainWindow UI to add functionality for the main tool window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle(f'Vine Markdown Editor {importlib.metadata.version("vine")}')

        # TODO: Persist these settings to a user's config file.
        self.settings = Settings(headings=HeadingFormat.BARS)
        self._show_settings()

        self.ui.actionNew.triggered.connect(self.new)
        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.actionSave.triggered.connect(lambda: self.ui.tabs.currentWidget().save())
        self.ui.actionSave_As.triggered.connect(lambda: self.ui.tabs.currentWidget().save_as())
        self.ui.actionSave_a_Copy.triggered.connect(lambda: self.ui.tabs.currentWidget().save_copy())
        self.ui.actionCloseTab.triggered.connect(lambda: self.close_tab(self.ui.tabs.currentIndex()))
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionHeadingsHashes.triggered.connect(lambda: self.headings(HeadingFormat.HASHES))
        self.ui.actionHeadingsBars.triggered.connect(lambda: self.headings(HeadingFormat.BARS))
        self.ui.actionInsert.triggered.connect(lambda: self.ui.tabs.currentWidget().insert())
        self.ui.actionDelete.triggered.connect(lambda: self.ui.tabs.currentWidget().delete())
        self.ui.actionAbout.triggered.connect(self.about)
        self.ui.actionPrint.triggered.connect(lambda: self.ui.tabs.currentWidget().on_print())
        self.ui.actionPreview.triggered.connect(lambda: self.ui.tabs.currentWidget().preview())
        self.ui.actionExportHtmlWhite.triggered.connect(lambda: self.ui.tabs.currentWidget().export_html('white'))
        self.ui.actionExportHtmlSlate.triggered.connect(lambda: self.ui.tabs.currentWidget().export_html('slate'))
        self.ui.tabs.tabCloseRequested.connect(self.close_tab)
        self.ui.tabs.currentChanged.connect(self.tab_changed)

        self.tab_changed()


# ----------------------------------------------------------------------------------------------------------------------
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Hook the GUI close event to try to warn the user about unsaved changes to open documents.

        See the docstring for the warn_all method to find out more about what it does.  If it returns False then the
        close event will be cancelled - leaving the main window open.
        """
        if self.warn_all():
            event.accept()
        else:
            event.ignore()


# ----------------------------------------------------------------------------------------------------------------------
    def close_tab(self, index: int) -> None:
        """Event fires when the user clicks the tab close button or uses the close tab option in the File menu.

        Arguments:
            index: The index of the tab to be closed.  If index is less than 0 (indicating there are no tabs left to
                close) then a request will be made to close the GUI window.
        """
        # If no tab was specified, close the GUI.  This should only really happen when there are no tabs left.
        if index < 0:
            self.close()

        # Close the specified tab.
        else:
            tab = self.ui.tabs.widget(index)

            # Provide the user with the opportunity to save before closing the tab.  Warn will return True if the user
            # has either elected to discard changes or saved them.  It returns False when the user has aborted.
            if tab.warn():
                self.ui.tabs.removeTab(index)

                # If this was the last tab manually fire the change event to disable actions.
                if self.ui.tabs.count() == 0:
                    self.tab_changed(None)


# ----------------------------------------------------------------------------------------------------------------------
    def tab_changed(self, index: int = None) -> None:
        """Fires when the currently selected tab changes.

        Arguments:
            index: The index of the newly selected tab or None when no tab is selected (e.g. at init).
        """
        # Update the actions in the file and edit menus.  Can't save or edit a lack of document.
        selected = index is not None
        self.ui.actionSave.setEnabled(selected)
        self.ui.actionSave_As.setEnabled(selected)
        self.ui.actionSave_a_Copy.setEnabled(selected)
        self.ui.actionPrint.setEnabled(selected)
        self.ui.actionPreview.setEnabled(selected)
        self.ui.menuEdit.setEnabled(selected)
        self.ui.menuExport.setEnabled(selected)


# ----------------------------------------------------------------------------------------------------------------------
    def warn_all(self) -> bool:
        """Warn the user that there are unsaved changes and prompt them to save before continuing.

        This method will loop through all of the open tabs and offer the user the option to save, discard, or abort the
        close for each file with unsaved changes.

        If the user selects "No to All" then changes to any remaining files will be discarded and the method will return
        True indicating the user is satisfied.

        If the user selects "Tes to All" then the prompts will stop and `save` will be called on all remaining files.
        If any of the remaining files do not have a filename then the user will be prompted for where to save the new
        file and should the user cancel that save dialog the saving operation will be halted and the window will remain
        open.

        Returns:
            True if the user has acknowledged the unsaved changes and processing should continue of False if the user
            has cancelled and the caller should cease what it was doing.
        """
        yes_all = False

        for idx in range(self.ui.tabs.count()):
            self.ui.tabs.setCurrentIndex(idx)
            tab = self.ui.tabs.widget(idx)
            if tab.model.dirty(self.settings):
                if yes_all:
                    # Once the user selected "Yes to All" then we can plow through the remainder and just assume save.
                    result = QtWidgets.QMessageBox.Save

                else:
                    # Prompt the user for an action on this file.
                    flags = QtWidgets.QMessageBox.Abort
                    flags |= QtWidgets.QMessageBox.Yes
                    flags |= QtWidgets.QMessageBox.YesToAll
                    flags |= QtWidgets.QMessageBox.No
                    flags |= QtWidgets.QMessageBox.NoToAll
                    message = 'Save changes to '
                    if tab.filename:
                        message += f'"{os.path.basename(tab.filename)}"?\n\n'
                        message += os.path.abspath(tab.filename)
                    else:
                        message += 'untitled file?'
                    result = QtWidgets.QMessageBox.critical(self, 'Save changes', message, flags)

                    # "Yes to All" is a special case that will not prompt the user to save any more changes.
                    if result == QtWidgets.QMessageBox.YesToAll:
                        result = QtWidgets.QMessageBox.Yes
                        yes_all = True

                # If they sad "save" then lets try to save them.
                if result == QtWidgets.QMessageBox.Save:
                    if not tab.save():
                        # If the user cancels out of a save then abort the operation to give them another try.
                        return False

                # If then cancelled then abort the entire operation.
                elif result == QtWidgets.QMessageBox.Abort:
                    return False

                # If the user selects "No to All" then break the loop and return True to close the window.
                elif result == QtWidgets.QMessageBox.NoToAll:
                    return True

        # If they make it through all of the tabs then we're good to allow closing - everything is clean.
        return True


# ----------------------------------------------------------------------------------------------------------------------
    def new(self) -> TabWidget:
        """Create a new, empty tab and document for editing.

        Returns:
            The newly created TabWidget instance, primarily intended for the open method to load a document.
        """
        tab = TabWidget(self)
        self.ui.tabs.addTab(tab, 'untitled')
        self.ui.tabs.setCurrentWidget(tab)

        def content_changed() -> None:
            """Connected to the contentChanged event of the new tab to update the tab title when the user changes the
            contents.
            """
            dirty = '*' if tab.model.dirty(self.settings) else ''
            filename = os.path.splitext(os.path.basename(tab.filename))[0] if tab.filename else 'untitled'
            index = self.ui.tabs.indexOf(tab)
            self.ui.tabs.setTabText(index, f'{dirty}{filename}')
            self.ui.tabs.setTabToolTip(index, os.path.abspath(tab.filename) if tab.filename else '')

        def selection_changed(selection: QtCore.QItemSelection) -> None:
            """Connected to the tree selection changes in the tab.

            Adjusts the availability of the options in the edit menu according to the new selection.
            """
            self.ui.actionDelete.setEnabled(len(selection) == 1)
            self.ui.actionInsert.setEnabled(tab.article.level < 6)

        tab.selectionChanged.connect(selection_changed)
        tab.contentChanged.connect(content_changed)

        return tab


# ----------------------------------------------------------------------------------------------------------------------
    def open(self):
        """Launch an open file dialog and select a new document to open in a tab."""
        filters = [
            'Markdown (*.md *.mkd *.mdwn *.mdown *.markdown *.mdtxt *.mdtext *.workbook)',
            'XML (*.xml)'
        ]
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, filter=';;'.join(filters))
        if filename:
            tab = self.new()
            tab.open(filename)


# ----------------------------------------------------------------------------------------------------------------------
    def about(self):
        """Show an about dialog with information about this tool."""
        title = 'About Vine Markdown Editor'
        description = importlib.metadata.metadata('vine')['Summary'] + '\n\n'
        description += 'Author: ' + importlib.metadata.metadata('vine')['Author']
        description += ' <' + importlib.metadata.metadata('vine')['Author-email'] + '>\n'
        description += 'Copyright: (c) 2022 ' + importlib.metadata.metadata('vine')['Author']
        QtWidgets.QMessageBox.about(self, title, description)


# ----------------------------------------------------------------------------------------------------------------------
    def _show_settings(self) -> None:
        """Updates the settings menu to display the current settings."""
        self.ui.actionHeadingsHashes.setChecked(self.settings.headings == HeadingFormat.HASHES)
        self.ui.actionHeadingsBars.setChecked(self.settings.headings == HeadingFormat.BARS)


# ----------------------------------------------------------------------------------------------------------------------
    def headings(self, format: HeadingFormat) -> None:
        """Fires when the user changes the setting for headings.

        Arguments:
            format: The newly selecting heading format to use.
        """
        self.settings.headings = HeadingFormat(format)
        self._show_settings()




# End of File
