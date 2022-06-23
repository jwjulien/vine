# ======================================================================================================================
#      File:  /vine/gui/widgets/editor/action.py
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
"""An action to connect a QTextEdit to the enchant spell checker whenever text is changed."""

# ======================================================================================================================
# Imports
# ----------------------------------------------------------------------------------------------------------------------
from PySide6 import QtCore, QtGui



# ======================================================================================================================
# Spell Correction Action Class
# ----------------------------------------------------------------------------------------------------------------------
class SpellAction(QtGui.QAction):
    """A special QAction that returns the text as a signal.
    
    This action allows a connection to the spell checker so that the text can be evaluated as it is entered.
    """
    correct = QtCore.Signal(str)

    def __init__(self, word, parent, label=None):
        QtGui.QAction.__init__(self, label or word, parent)
        self.triggered.connect(lambda x: self.correct.emit(word))




# End of File
