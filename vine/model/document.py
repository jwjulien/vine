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
from vine.settings import HeadingFormat, Settings




# ======================================================================================================================
# Document Class
# ----------------------------------------------------------------------------------------------------------------------
class Document:

    def __init__(self):
        super().__init__()
        self.root: Article = Article('root', '')
        self._cached = ''


# ----------------------------------------------------------------------------------------------------------------------
    def load(self, filename: str):
        """Load a document from file."""
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
            title, body = content.split('\n', 1)
            child = Article(title=title.rstrip('#').strip(), body=body.strip(), parent=parent)
            parent.children.append(child)


# ----------------------------------------------------------------------------------------------------------------------
    def dump(self, filename: str, settings: Settings) -> None:
        """Write the contents of this model to the provided filename.

        Arguments:
            filename: The path and name of the file to which the contents of this Document are to be dumped.
            headings: The format to use for the headings in the output file.
        """
        document = self.dumps(settings)
        with open(filename, 'w', encoding='utf-8') as handle:
            handle.write(document)
        self._cached = document


# ----------------------------------------------------------------------------------------------------------------------
    def dumps(self, settings: Settings) -> str:
        """Return the contents of this document as a sting."""
        def dump_node(root: Article) -> str:
            text = ''

            for article in root.children:
                # Prepend newlines BEFORE this section.
                text += max(2, 7 - article.level) * '\n'

                # Generate a heading based upon the specified heading format.
                if settings.headings == HeadingFormat.HASHES or article.level > 2:
                    text += ('#' * article.level) + ' '
                text += article.title.strip()
                if settings.headings == HeadingFormat.BARS:
                    if article.level == 1:
                        text += '\n' + ('=' * 120)
                    elif article.level == 2:
                        text += '\n' + ('-' * 120)
                    elif article.level == 3:
                        text += ' ' + ('#' * (120 - len(article.title.strip()) - article.level - 2))
                    elif article.level == 4:
                        text += ' ' + ('#' * 4)
                text += '\n'

                # Append the body text.
                text += article.body.rstrip('\n')

                # Recurse into children, when applicable (returns nothing when this is a leaf node).
                text += dump_node(article)

            return text

        return dump_node(self.root).strip('\n')


# ----------------------------------------------------------------------------------------------------------------------
    def dirty(self, settings: Settings) -> bool:
        current = self.dumps(settings)
        return current != self._cached


# ----------------------------------------------------------------------------------------------------------------------
    def to_html(self, settings: Settings) -> str:
        text = self.dumps(settings)
        extensions = [
            'admonition',
            'codehilite',
            'extra'
        ]
        html = markdown(text, extensions=extensions)
        return html


# ----------------------------------------------------------------------------------------------------------------------
    def clear(self):
        self.root.clear()
        self._cached = ''


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
