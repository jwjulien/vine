# ======================================================================================================================
#      File:  /vine/gui/widgets/editor/editor.py
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

# ======================================================================================================================
# Import Statements
# ----------------------------------------------------------------------------------------------------------------------
from PySide6 import QtCore, QtGui, QtWidgets
import enchant

from vine.gui.widgets.editor.highlighter import MarkdownSpellHighlighter
from vine.gui.widgets.editor.action import SpellAction




# ======================================================================================================================
# Markdown Spell Text Edit Class
# ----------------------------------------------------------------------------------------------------------------------
class MarkdownSpellTextEdit(QtWidgets.QPlainTextEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.installEventFilter(self)
        self.viewport().installEventFilter(self)

        self.highlighter = MarkdownSpellHighlighter(self.document())

        self.set_tab_stop(4)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        self.setLayout(layout)

        self.textChanged.connect(self.adjust_right_margin)

        self.dict = enchant.Dict("en_US")
        self.highlighter.set_dict(self.dict)


# ----------------------------------------------------------------------------------------------------------------------
    def mousePressEvent(self, event):
        """Override the mouse press event, detect if it was a right click, and adjust the cursor position."""
        if event.button() == QtCore.Qt.RightButton:
            # Rewrite the mouse event to a left button event so the cursor is moved to the location of the pointer.
            event = QtGui.QMouseEvent(QtCore.QEvent.MouseButtonPress, event.pos(),
                QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier)
        QtWidgets.QPlainTextEdit.mousePressEvent(self, event)


# ----------------------------------------------------------------------------------------------------------------------
    def contextMenuEvent(self, event):
        """Generate a context menu when the user right clicks and include a list of spelling corrections, where
        appropriate."""
        # Select the word under the cursor.
        cursor = self.textCursor()
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
        self.setTextCursor(cursor)

        # Check if the selected word is misspelled and offer spelling suggestions if it is.
        if self.textCursor().hasSelection():
            text = self.textCursor().selectedText()
            menu = QtWidgets.QMenu()
            if not self.dict.check(text):
                for word in self.dict.suggest(text):
                    action = SpellAction(word, menu)
                    action.correct.connect(self.correct_word)
                    menu.addAction(action)

            if len(menu.actions()) == 0:
                # When there are no suggestions then add some non-functional text to the menu to at least inform the
                # user of the same.
                menu.addAction('No Suggestions')

            else:
                # When there was at least one suggestion, then present the user with options to ignore the suggestion.
                menu.addSeparator()

                # Give the option to ignore the misspelling for the current session.
                session = SpellAction(text, menu, f'Ignore "{text}" for current session')
                session.correct.connect(self.ignore_session)
                menu.addAction(session)

                # Give another option to add the word to the user's personal dictionary.
                personal = SpellAction(text, menu, f'Add "{text}" to dictionary')
                personal.correct.connect(self.add_to_dictionary)
                menu.addAction(personal)

            menu.exec_(event.globalPos())


# ----------------------------------------------------------------------------------------------------------------------
    def ignore_session(self, word):
        """Adds a word to the session dictionary when selected from the menu by the user.  This will ignore the provided
        word for the remainder of time that the program is run."""
        self.dict.add_to_session(word)
        self.underliner.rehighlight()


# ----------------------------------------------------------------------------------------------------------------------
    def add_to_dictionary(self, word):
        """Adds a word to the user's personal dictionary.  This file is located in the user's private settings which
        means that the word will never be shown again as being misspelled by that user."""
        self.dict.add(word)
        self.underliner.rehighlight()


# ----------------------------------------------------------------------------------------------------------------------
    def correct_word(self, word):
        """Replaces the selected text with word."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertText(word)
        cursor.endEditBlock()


# ----------------------------------------------------------------------------------------------------------------------
    def set_tab_stop(self, spaces):
        """Helper function to set the tab stop width to an integer number to space characters."""
        font = self.font()
        metrics = QtGui.QFontMetrics(font)
        self.setTabStopDistance(spaces * metrics.tightBoundingRect(' ').width())


# ----------------------------------------------------------------------------------------------------------------------
    def adjust_right_margin(self):
        """Called whenever the text changes to setup the right margin."""
        margins = self.layout().contentsMargins()
        rightMargin = 24 if self.document().size().height() > self.viewport().size().height() else 0
        margins.setRight(rightMargin)
        self.layout().setContentsMargins(margins)


# ----------------------------------------------------------------------------------------------------------------------
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.HoverMove:
            viewPort = self.viewport()

            # toggle cursor when control key has been pressed or released
            if bool(event.modifiers() & QtCore.Qt.ControlModifier):
                cursor = QtCore.Qt.PointingHandCursor
            else:
                cursor = QtCore.Qt.IBeamCursor
            viewPort.setCursor(cursor)

        elif event.type() == QtCore.QEvent.KeyPress:
            # Set cursor to pointing hand if control key was pressed.
            if bool(event.modifiers() & QtCore.Qt.ControlModifier):
                self.viewport().setCursor(QtCore.Qt.PointingHandCursor)

            # Disallow keys if text edit doesn't have focus.
            if not self.hasFocus():
                return True

            elif event.key() == QtCore.Qt.Key_Asterisk:
                return self._handle_bracket_closing("*")

            elif event.key() == QtCore.Qt.Key_QuoteDbl:
                return self._quotation_mark_check("\"")

            elif event.key() == QtCore.Qt.Key_QuoteLeft:
                return self._quotation_mark_check("`")

            elif event.key() == QtCore.Qt.Key_AsciiTilde:
                return self._handle_bracket_closing("~")

            elif event.key() == QtCore.Qt.Key_ParenLeft:
                return self._handle_bracket_closing("(", ")")

            elif event.key() == QtCore.Qt.Key_BraceLeft:
                return self._handle_bracket_closing("{", "}")

            elif event.key() == QtCore.Qt.Key_BracketLeft:
                return self._handle_bracket_closing("[", "]")

            elif event.key() == QtCore.Qt.Key_Less:
                return self._handle_bracket_closing("<", ">")

            elif event.key() == QtCore.Qt.Key_ParenRight:
                return self._bracket_closing_check("(", ")")

            elif event.key() == QtCore.Qt.Key_BraceRight:
                return self._bracket_closing_check("{", "}")

            elif event.key() == QtCore.Qt.Key_BracketRight:
                return self._bracket_closing_check("[", "]")

            elif event.key() == QtCore.Qt.Key_Return and bool(event.modifiers() & QtCore.Qt.ShiftModifier):
                cursor = self.textCursor()
                cursor.insertText("  \n")
                return True

            elif event.key() == QtCore.Qt.Key_Return and bool(event.modifiers() & QtCore.Qt.ControlModifier):
                cursor = self.textCursor()
                cursor.movePosition(QtGui.QTextCursor.EndOfLine)
                cursor.insertText("\n")
                self.setTextCursor(cursor)
                return True

            elif event == QtGui.QKeySequence.Copy or event == QtGui.QKeySequence.Cut:
                cursor = self.textCursor()
                if not cursor.hasSelection():
                    if cursor.block().length() <= 1:
                        # no content
                        text = "\n"
                    else:
                        #cursor.select(QTextCursor::BlockUnderCursor) # negative, it will include the previous paragraph separator
                        cursor.movePosition(QtGui.QTextCursor.StartOfBlock)
                        cursor.movePosition(QtGui.QTextCursor.EndOfBlock, QtGui.QTextCursor.KeepAnchor)
                        text = cursor.selectedText()
                        if not cursor.atEnd():
                            text += "\n"
                            # This is the paragraph separator.
                            cursor.movePosition(QtGui.QTextCursor.NextCharacter, QtGui.QTextCursor.KeepAnchor, 1)

                    if event == QtGui.QKeySequence.Cut:
                        if not cursor.atEnd() and text == "\n":
                            cursor.deletePreviousChar()
                        else:
                            cursor.removeSelectedText()
                        cursor.movePosition(QtGui.QTextCursor.StartOfLine)
                        self.setTextCursor(cursor)

                    QtGui.QGuiApplication.clipboard().setText(text)
                    return True

            elif event == QtGui.QKeySequence.Paste:
                if QtGui.QGuiApplication.clipboard().ownsClipboard():
                    # Any clip that ends with a single newline - paste it at the beginning of this line.
                    text = QtGui.QGuiApplication.clipboard().text()
                    if QtCore.QRegularExpression("[^\n]*\n$").match(text).hasMatch():
                        cursor = self.textCursor()
                        if not cursor.hasSelection():
                            cursor.movePosition(QtGui.QTextCursor.StartOfLine)
                            self.setTextCursor(cursor)

            elif event.key() == QtCore.Qt.Key_Down and bool(event.modifiers() & QtCore.Qt.ControlModifier) and bool(event.modifiers() & QtCore.Qt.AltModifier):
                # Duplicate text with `Ctrl + Alt + Down`.
                self._duplicate_text()
                return True

            elif event.key() == QtCore.Qt.Key_Down and bool(event.modifiers() & QtCore.Qt.NoModifier):
                # If you are in the last line and press cursor down the cursor will jump to the end of the line.
                cursor = self.textCursor()
                if cursor.position() >= self.document().lastBlock().position():
                    cursor.movePosition(QtGui.QTextCursor.EndOfLine)
                    self.setTextCursor(cursor)

                return False

            elif event.key() == QtCore.Qt.Key_Up and bool(event.modifiers() & QtCore.Qt.NoModifier):
                # If you are in the first line and press cursor up the cursor will jump to the start of the line.
                cursor = self.textCursor()
                block = self.document().firstBlock()
                endOfFirstLinePos = block.position() + block.length()

                if cursor.position() <= endOfFirstLinePos:
                    cursor.movePosition(QtGui.QTextCursor.StartOfLine)
                    self.setTextCursor(cursor)

                return False

            return False

        elif event.type() == QtCore.QEvent.KeyRelease:
            # Reset cursor if control key was released.
            if event.key() == QtCore.Qt.Key_Control:
                self._reset_mouse_cursor()

            return False

        elif event.type() == QtCore.QEvent.MouseButtonRelease:
            # Track `Ctrl + Click` in the text edit.
            if obj == self.viewport() and event.button() == QtCore.Qt.LeftButton and QtGui.QGuiApplication.keyboardModifiers() == QtCore.Qt.ExtraButton24:
                # Open the link (if any) at the current position.
                self.open_link_at_cursor_position()

                return True

        return super().eventFilter(obj, event)


# ----------------------------------------------------------------------------------------------------------------------
    def focusOutEvent(self, event):
        self._reset_mouse_cursor()
        super().focusOutEvent(event)


# ----------------------------------------------------------------------------------------------------------------------
    def _reset_mouse_cursor(self):
        self.viewport().setCursor(QtCore.Qt.IBeamCursor)


# ----------------------------------------------------------------------------------------------------------------------
    def _handle_bracket_closing(self, opening, closing=None):
        cursor = self.textCursor()

        if closing is None:
            closing = opening

        text = cursor.selectedText()

        if text:
            # If text was selected, wrap it with the provided brackets.
            cursor.insertText(opening)
            cursor.insertText(text)
            cursor.insertText(closing)
            return True

        else:
            position = cursor.position() - cursor.block().position()

            # Only allow the closing if the cursor was not at the end of a block, specifically allow '*' at end though.
            if position != len(text) and opening != '*' and position != (len(text) - 1):
                return False

        text = text.lstrip()

        subtract = 1

        # Special handling of '*' for start of list, sublist, or bold text.
        if opening == '*':
            if not text:
                # User wants '*'
                return False

            elif text == '*':
                # User wants '**'
                closing = '**'
                subtract = 2

            elif text == '* ':
                # User wants '* *'  -we are in a list already, proceed as normal.
                pass

        # Auto-completion for ``` pair.
        if opening == '`':
            if QtCore.QRegularExpression(r'[&`]*``').match(text).hasMatch():
                cursor.insertText(opening)
                cursor.insertText(opening)
                subtract = 3

        cursor.insertText(opening)
        cursor.insertText(closing)
        cursor.setPosition(cursor.position() - subtract)
        self.setTextCursor(cursor)
        return True


# ----------------------------------------------------------------------------------------------------------------------
    def _bracket_closing_check(self, opening, closing=None):
        if closing is None:
            closing = opening

        cursor = self.textCursor()
        position = cursor.position() - cursor.block().position()
        text = cursor.block().text()

        # If we are at the end of the line then just enter the character.
        if position >= len(text):
            return

        if text[position] == closing:
            return False

        left = text[:position]
        if left.count(opening) < left.count(closing) + 1:
            # If there were enough opening characters then just enter the character.
            return False

        cursor.movePosition(QtGui.QTextCursor.Right)
        self.setTextCursor(cursor)
        return True


# ----------------------------------------------------------------------------------------------------------------------
    def _quotation_mark_check(self, quote):
        cursor = self.textCursor()
        position = cursor.position() - cursor.block().position()
        text = cursor.block().text()

        # If at the end of the line or if the current character is not the quote character, just enter the character.
        if position >= len(text) or text[position] != quote:
            return self._handle_bracket_closing(quote)

        cursor.movePosition(QtGui.QTextCursor.Right)
        self.setTextCursor(cursor)
        return True


# ----------------------------------------------------------------------------------------------------------------------
    def _open_link_at_cursor_position(self):
        cursor = self.textCursor()
        position = cursor.position()
        cursor.movePosition(QtGui.QTextCursor.StartOfBlock)
        positionFromStart = position - cursor.position()
        cursor.movePosition(QtGui.QTextCursor.EndOfBlock, QtGui.QTextCursor.KeepAnchor)
        text = cursor.selectedText()
        # TODO: Bring in the rest of this convoluted logic and launch a webbrowser with the proper link.
        return False


# ----------------------------------------------------------------------------------------------------------------------
    def _duplicate_text(self):
        cursor = self.textCursor()
        text = cursor.selectedText()
        if not text:
            # Duplicate the line if no text was selected.
            position = cursor.position()
            cursor.movePosition(QtGui.QTextCursor.StartOfLine)
            cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
            difference = cursor.position() - position
            text = '\n' + cursor.selectedText()
            cursor.setPosition(cursor.selectionEnd())
            cursor.insertText(text)
            cursor.setPosition(cursor.position() - difference)

        else:
            # Duplicate the selection.
            cursor.setPosition(cursor.selectionEnd())
            start = cursor.position()
            cursor.insertText(text)
            end = cursor.position()
            cursor.setPosition(start)
            cursor.setPosition(end, QtGui.QTextCursor.KeepAnchor)

        self.setTextCursor(cursor)


# ----------------------------------------------------------------------------------------------------------------------
    def setPlainText(self, text):
        self.highlighter.clear_dirty_blocks()
        super().setPlainText(text)
        self.adjust_right_margin()




# End of File
