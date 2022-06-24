# ======================================================================================================================
#      File:  /vine/model/article.py
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
"""An Article represents a single page in the tree structure consisting of a title and body of text."""

# ======================================================================================================================
# Imports
# ----------------------------------------------------------------------------------------------------------------------
from typing import List




# ======================================================================================================================
# Article Class
# ----------------------------------------------------------------------------------------------------------------------
class Article:
    """Represents an "item" in the document tree containing the title and body text information.

    Attributes:
        title: The title of this article to be used as a heading in the document section.
        body: Markdown body text for this section of the document.
    """
    def __init__(self, title: str, body: str, parent: 'Article' = None):
        self.title = title
        self.body = body
        self.parent: 'Article' = parent
        self.children: List['Article'] = []

    def clear(self) -> None:
        self.children = []

    def child(self, number: int) -> 'Article':
        if number < 0 or number >= len(self.children):
            return None
        return self.children[number]

    def last_child(self) -> 'Article':
        return self.children[-1] if self.children else None

    def child_count(self) -> int:
        return len(self.children)

    def sibling_number(self) -> int:
        if self.parent:
            return self.parent.children.index(self)
        return 0

    def __repr__(self) -> str:
        return f'<Article at 0x{id(self):x} title="{self.title}">'




# End of File
