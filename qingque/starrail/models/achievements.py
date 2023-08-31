"""
MIT License

Copyright (c) 2023-present naoTimesdev

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

from msgspec import field

from .base import SRSBase

__all__ = ("SRSAchievement",)


class SRSAchievement(SRSBase, frozen=True):
    id: str
    """:class:`str`: The achievement ID."""
    series_id: str
    """:class:`str`: The series ID."""
    title: str
    """:class:`str`: The achievement title."""
    description: str = field(name="desc", default="")
    """:class:`str`: The achievement description."""
    hidden_description: str = field(name="hide_desc", default="")
    """:class:`str`: The hidden achievement description."""
    hide: bool = field(default=False)
    """:class:`bool`: Whether the achievement is hidden."""
