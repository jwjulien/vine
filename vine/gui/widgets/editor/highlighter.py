# ======================================================================================================================
#      File:  /vine/gui/widgets/editor/highlighter.py
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
from dataclasses import dataclass
from enum import IntEnum
import re

from PySide6 import QtCore, QtGui




# ======================================================================================================================
# Highlight State Enumeration
# ----------------------------------------------------------------------------------------------------------------------
class HighlighterState(IntEnum):
    """Definitions for the various forms of syntax to be highlighted by this editor."""
    Default = 0
    Link = 1
    Image = 2
    CodeBlock = 3
    Italic = 4
    Bold = 5
    List = 6
    Comment = 7
    H1 = 8
    H2 = 9
    H3 = 10
    H4 = 11
    H5 = 12
    H6 = 13
    BlockQuote = 14
    HorizontalRuler = 15
    Table = 16
    InlineCodeBlock = 17
    MaskedSyntax = 18
    CurrentLineBackgroundColor = 19
    BrokenLink = 20
    CodeBlockEnd = 21
    HeadlineEnd = 22




# ======================================================================================================================
# Highlight Rule Class
# ----------------------------------------------------------------------------------------------------------------------
@dataclass
class HighlightRule:
    """A grouping of attributes that make up a rule for highlighting syntax.

    Attributes:
        state: Specifies the "state" that will be used to map to a highlighter upon matching the `pattern`.
        pattern: Regular expression syntax to match the rule in the markdown text.
        capturing: ?
        masked:
    """
    state: HighlighterState
    pattern: str
    capturing: int = 0
    masked: int = 0
    useState: bool = False
    disable: bool = False




# ======================================================================================================================
# Markdown Highlighter Class
# ----------------------------------------------------------------------------------------------------------------------
class MarkdownSpellHighlighter(QtGui.QSyntaxHighlighter):
    """This is an amalgamation of the spell check extension to the QPlainTextEdit widget and the Markdown extension of
    the same.  This provides the same spell checking properties, on top of Markdown syntax highlighting."""
    WORDS = r"(?iu)[\w']+"

    def __init__(self, parent):
        super().__init__(parent)

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.timer_tick)
        self._timer.start(1000)

        self._pre_rules = []
        self._post_rules = []
        self._init_rules()

        self._formats = {}
        self._init_formats(12)

        self._dirtyBlocks = []

        self.dict = None


# ----------------------------------------------------------------------------------------------------------------------
    def set_dict(self, dict):
        """Setup the enchant dictionary for use with this highlighter."""
        self.dict = dict


# ----------------------------------------------------------------------------------------------------------------------
    def _init_rules(self):
        """Initialize the rule set for Markdown syntax."""
        self._pre_rules.append(HighlightRule(HighlighterState.MaskedSyntax, r'(^\[.+?\]: \w+:#.+$)'))
        self._pre_rules.append(HighlightRule(HighlighterState.List, r'^\s*[-*+]\s', useState=True))
        self._pre_rules.append(HighlightRule(HighlighterState.List, r'(^\s*\d+\.\s)', useState=True))
        self._pre_rules.append(HighlightRule(HighlighterState.BlockQuote, r'^\s*(>\s*.+)'))
        self._pre_rules.append(HighlightRule(HighlighterState.HorizontalRuler, r'^([*\-_]\s?){3,}$'))

        self._post_rules.append(HighlightRule(HighlighterState.Italic, r'((?:^|[^\*\b])(?:\*([^\* ][^\*]*?)\*)(?:[^\*\b]|$))', capturing=1))
        self._post_rules.append(HighlightRule(HighlighterState.Italic, r'\b_([^_]+)_\b', capturing=1))
        self._post_rules.append(HighlightRule(HighlighterState.Bold, r'(\B\*{2}(.+?)\*{2}\B)', capturing=1))
        self._post_rules.append(HighlightRule(HighlighterState.Bold, r'\b__(.+?)__\b', capturing=1))
        self._post_rules.append(HighlightRule(HighlighterState.Link, r'(\b\w+?:\/\/[^\s]+)', capturing=0))
        self._post_rules.append(HighlightRule(HighlighterState.Link, r'<([^\s`][^`]*?[^\s`])>', capturing=1))
        self._post_rules.append(HighlightRule(HighlighterState.Link, r'(\[([^\[\]]+)\]\((\S+|.+?)\)\B)', capturing=1))
        self._post_rules.append(HighlightRule(HighlighterState.Link, r'(\[\]\((.+?)\))', capturing=1))
        self._post_rules.append(HighlightRule(HighlighterState.Link, r'<(.+?@.+?)>', capturing=1))
        self._post_rules.append(HighlightRule(HighlighterState.Link, r'(\[(.+?)\]\s?\[.+?\])', capturing=1))
        self._post_rules.append(HighlightRule(HighlighterState.Image, r'(!\[(.+?)\]\(.+?\))', capturing=1))
        self._post_rules.append(HighlightRule(HighlighterState.Image, r'(!\[\]\((.+?)\))', capturing=1))
        self._post_rules.append(HighlightRule(HighlighterState.Link, r'(\[!\[(.+?)\]\(.+?\)\]\(.+?\))', capturing=1))
        self._post_rules.append(HighlightRule(HighlighterState.Link, r'(\[!\[\]\(.+?\)\]\((.+?)\))', capturing=1))
        self._post_rules.append(HighlightRule(HighlighterState.InlineCodeBlock, r'`(.+?)`', capturing=1))
        self._post_rules.append(HighlightRule(HighlighterState.CodeBlock, r'^((\t)|( {4,})).+$', disable=True))
        self._post_rules.append(HighlightRule(HighlighterState.Comment, r'(<!\-\-(.+?)\-\->)', capturing=1))
        self._post_rules.append(HighlightRule(HighlighterState.Comment, r'(^\[.+?\]: # \(.+?\)$)', capturing=1))
        self._post_rules.append(HighlightRule(HighlighterState.Table, r'^\|.+?\|$'))


# ----------------------------------------------------------------------------------------------------------------------
    def _init_formats(self, fontSize):
        """Initialize the text formats used by the highlighter."""
        def build(foreground=None, background=None, fixed=False, size=None, bold=False, italic=False, underline=False):
            """Helper function to build Qt font formats from some common, limited parameters."""
            textFormat = QtGui.QTextCharFormat()
            if foreground is not None:
                textFormat.setForeground(QtGui.QBrush(foreground))
            if background is not None:
                textFormat.setBackground(QtGui.QBrush(background))
            if bold:
                textFormat.setFontWeight(QtGui.QFont.Bold)
            if italic:
                textFormat.setFontWeight(QtGui.QFont.StyleItalic)
                textFormat.setFontItalic(italic)
            textFormat.setFontUnderline(underline)
            textFormat.setFontFixedPitch(fixed)
            if size is not None:
                textFormat.setFontPointSize(size)
            return textFormat

        Color = QtGui.QColor
        headingColor = Color(0, 49, 110)
        codeColor = Color(220, 220, 220)
        self._formats['H1'] = build(foreground=headingColor, bold=True, size=(fontSize * 1.6))
        self._formats['H2'] = build(foreground=headingColor, bold=True, size=(fontSize * 1.5))
        self._formats['H3'] = build(foreground=headingColor, bold=True, size=(fontSize * 1.4))
        self._formats['H4'] = build(foreground=headingColor, bold=True, size=(fontSize * 1.3))
        self._formats['H5'] = build(foreground=headingColor, bold=True, size=(fontSize * 1.2))
        self._formats['H6'] = build(foreground=headingColor, bold=True, size=(fontSize * 1.1))
        self._formats['HorizontalRuler'] = build(foreground=QtCore.Qt.darkGray, background=QtCore.Qt.lightGray)
        self._formats['List'] = build(foreground=Color(163, 0, 123))
        self._formats['Link'] = build(foreground=Color(0, 128, 255), underline=True)
        self._formats['Image'] = build(foreground=Color(0, 191, 0), background=Color(228, 255, 228))
        self._formats['CodeBlock'] = build(fixed=True, background=codeColor)
        self._formats['InlineCodeBlock'] = build(fixed=True, background=codeColor)
        self._formats['Italic'] = build(italic=True)
        self._formats['Bold'] = build(bold=True)
        self._formats['Comment'] = build(foreground=QtCore.Qt.gray)
        self._formats['MaskedSyntax'] = build(foreground=Color(204, 204, 204))
        self._formats['Table'] = build(fixed=True, foreground=Color(100, 148, 73))
        self._formats['BlockQuote'] = build(foreground=QtCore.Qt.darkRed)
        self._formats['HeadlineEnd'] = build()
        self._formats['Default'] = build()


# ----------------------------------------------------------------------------------------------------------------------
    def timer_tick(self):
        """Called periodically by the timer to re-highlight dirty blocks."""
        while self._dirtyBlocks:
            block = self._dirtyBlocks.pop(0)
            self.rehighlightBlock(block)


# ----------------------------------------------------------------------------------------------------------------------
    def add_dirty_block(self, block):
        """Add the provided block to the list of dirty blocks if it's not already in the list."""
        if block not in self._dirtyBlocks:
            self._dirtyBlocks.append(block)


# ----------------------------------------------------------------------------------------------------------------------
    def clear_dirty_blocks(self):
        """Clears out the list of dirty blocks.  This is used by the GUI to clear out the list when new text has been
        assigned to the control."""
        self._dirtyBlocks = []


# ----------------------------------------------------------------------------------------------------------------------
    def highlightBlock(self, text):
        """Overrides the highlightBlock of the QSyntaxHighlighter class to perform the actual highlighting of the
        provided text."""
        self.setCurrentBlockState(HighlighterState.Default)
        self.currentBlock().setUserState(HighlighterState.Default)

        if text:
            self._highlight_additional_rules(self._pre_rules, text)
            self._highlight_headline(text)
            self._highlight_additional_rules(self._post_rules, text)

        self._highlight_comment_block(text)
        self._highlight_code_block(text)
        self._highlight_misspelled(text)


# ----------------------------------------------------------------------------------------------------------------------
    def _highlight_additional_rules(self, rules, text):
        """Highlight a list of provided rules.  This function is actually called twice by highlightBlock but with two
        different rule sets, one before and one after the heading handling."""
        maskedFormat = self._formats['MaskedSyntax']

        for rule in rules:
            # continue if an other current block state was already set if disableIfCurrentStateIsSet is set
            if rule.disable and self.currentBlockState() != HighlighterState.Default:
                continue

            expression = QtCore.QRegularExpression(rule.pattern)
            iterator = expression.globalMatch(text)
            format = self._formats[rule.state.name]

            # store the current block state if useStateAsCurrentBlockState
            # is set
            if iterator.hasNext() and rule.useState:
                self.setCurrentBlockState(rule.state)

            # find and format all occurrences
            while iterator.hasNext():
                match = iterator.next()

                # if there is a capturing set then first highlight
                # everything as MaskedSyntax and highlight capturing
                # with the real format
                if rule.capturing:
                    currentMaskedFormat = maskedFormat.__copy__()

                    # set the font size from the current rule's font format
                    if format.fontPointSize():
                        currentMaskedFormat.setFontPointSize(format.fontPointSize())

                    self.setFormat(match.capturedStart(rule.masked),
                                   match.capturedLength(rule.masked),
                                   currentMaskedFormat)

                self.setFormat(match.capturedStart(rule.capturing), match.capturedLength(rule.capturing), format)


# ----------------------------------------------------------------------------------------------------------------------
    def _highlight_headline(self, text):
        """Perform highlighting specifically for headings (H1, H2, H3, H4, H5, and H6) as well as the special handling
        for H1 and H2 headings using `=` and `-` underlines, respectively.

        Headings are slightly special as, as compared to other formatting, as they are formatted to highlight the
        heading text while masking the hash or underline characters."""
        regex = QtCore.QRegularExpression(r'^(#+)\s+(.+?)\s*#*$')
        match = regex.match(text)
        maskedFormat = self._formats['MaskedSyntax']

        # check for headline blocks with # in front of them
        if match.hasMatch():
            count = len(match.captured(1))

            # we just have H1 to H6
            count = min(count, 6)

            state = HighlighterState.H1 + count - 1

            format = self._formats[f'H{count}']
            currentMaskedFormat = maskedFormat.__copy__()

            # set the font size from the current rule's font format
            currentMaskedFormat.setFontPointSize(format.fontPointSize())

            # first highlight everything as MaskedSyntax
            self.setFormat(match.capturedStart(), match.capturedLength(), currentMaskedFormat)

            # then highlight with the real format
            self.setFormat(match.capturedStart(2), match.capturedLength(2), format)

            self.setCurrentBlockState(state)
            self.currentBlock().setUserState(state)
            return

        # Take care of ==== and ---- headlines.
        patternH1 = QtCore.QRegularExpression("^=+$")
        patternH2 = QtCore.QRegularExpression("^-+$")
        previousBlock = self.currentBlock().previous()
        previousText = previousBlock.text().strip(' =-')

        # Check for ===== after a headline text and highlight as H1.
        if patternH1.match(text).hasMatch():
            if self.previousBlockState() in [HighlighterState.H1, HighlighterState.Default] and previousText:
                # set the font size from the current rule's font format
                currentMaskedFormat = maskedFormat.__copy__()
                currentMaskedFormat.setFontPointSize(self._formats['H1'].fontPointSize())

                self.setFormat(0, len(text), currentMaskedFormat)
                self.setCurrentBlockState(HighlighterState.HeadlineEnd)
                previousBlock.setUserState(HighlighterState.H1)

                # We want to re-highlight the previous block.  This must not done directly, but with a queue, otherwise
                # it will crash.  Setting the character format of the previous text, because this causes text to be
                # formatted the same way when writing after the text.
                self.add_dirty_block(previousBlock)

            return


        # Check for ----- after a headline text and highlight as H2.
        if patternH2.match(text).hasMatch():
            if self.previousBlockState() in [HighlighterState.H2, HighlighterState.Default] and previousText:
                # set the font size from the current rule's font format
                currentMaskedFormat = maskedFormat.__copy__()
                currentMaskedFormat.setFontPointSize(self._formats['H2'].fontPointSize())

                self.setFormat(0, len(text), currentMaskedFormat)
                self.setCurrentBlockState(HighlighterState.HeadlineEnd)
                previousBlock.setUserState(HighlighterState.H2)

                # We want to re-highlight the previous block.
                self.add_dirty_block(previousBlock)

            return

        nextBlock = self.currentBlock().next()
        nextBlockText = nextBlock.text()

        # Highlight as H1 if next block is =====.
        if patternH1.match(nextBlockText).hasMatch() or patternH2.match(nextBlockText).hasMatch():
            self.setFormat(0, len(text), self._formats['H1'])
            self.setCurrentBlockState(HighlighterState.H1)
            self.currentBlock().setUserState(HighlighterState.H1)


        # highlight as H2 if next block is -----
        if patternH2.match(nextBlockText).hasMatch():
            self.setFormat(0, len(text), self._formats['H2'])
            self.setCurrentBlockState(HighlighterState.H2)
            self.currentBlock().setUserState(HighlighterState.H2)


# ----------------------------------------------------------------------------------------------------------------------
    def _highlight_comment_block(self, text):
        """Called by highlightBlock method to specifically highlight HTML comments within the Markdown text.  HTML
        comments are effectively comments within the Markdown text as they will not be displayed on the HTML page when
        rendered."""
        highlight = False
        text = text.strip()
        start = '<!--'
        end = '-->'

        if text.startswith(start) and end in text:
            # Skip this case for some reason.
            return

        if text.startswith(start) or (not text.endswith(end) and self.previousBlockState() == HighlighterState.Comment):
            self.setCurrentBlockState(HighlighterState.Comment)
            highlight = True

        elif text.endswith(end):
            highlight = True

        if highlight:
            self.setFormat(0, len(text), self._formats['Comment'])


# ----------------------------------------------------------------------------------------------------------------------
    def _highlight_code_block(self, text):
        """Called by highlightBlock to specifically highlight code blocks.  Will highlight code blocs that begin with
        three backtick characters."""
        regex = QtCore.QRegularExpression(r'^```\w*?$')
        matches = regex.match(text)

        if matches.hasMatch():
            if self.previousBlockState() == HighlighterState.CodeBlock:
                self.setCurrentBlockState(HighlighterState.CodeBlockEnd)
            else:
                self.setCurrentBlockState(HighlighterState.CodeBlock)

            # set the font size from the current rule's font format
            maskedFormat = self._formats['MaskedSyntax'].__copy__()
            maskedFormat.setFontPointSize(self._formats['CodeBlock'].fontPointSize())

            self.setFormat(0, len(text), maskedFormat)

        elif self.previousBlockState() == HighlighterState.CodeBlock:
            self.setCurrentBlockState(HighlighterState.CodeBlock)
            self.setFormat(0, len(text), self._formats['CodeBlock'])


# ----------------------------------------------------------------------------------------------------------------------
    def _highlight_misspelled(self, text):
        """Called on every block of text, this function will break the words in the block into individual pieces and
        apply a red, squiggly underline on top of their current style if they are not found in the dictionary.

        Doing it this way allows the spell checker to play nicely with the Markdown formatter."""

        # If there's no dictionary to use for spell checking then we can't even try to check the text.
        if not self.dict:
            return

        # Break the text into individual words and step through each of them.
        for word in re.finditer(self.WORDS, text):
            # If the word isn't found in the Enchant dictionaries, then highlight it.
            if not self.dict.check(word.group()):
                # Apply the red underline format on top of the existing style for the word to preserve the Markdown
                # formatting.
                style = self.format(word.start())
                style.setUnderlineColor(QtCore.Qt.red)
                style.setUnderlineStyle(QtGui.QTextCharFormat.SpellCheckUnderline)
                self.setFormat(word.start(), word.end() - word.start(), style)




# End of File
