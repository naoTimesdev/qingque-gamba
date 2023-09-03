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

from .base import MihomoBase

__all__ = (
    "SRSSimUniverseBlessing",
    "SRSSimUniverseCurio",
)


class SRSSimUniverseBlessing(MihomoBase, frozen=True):
    id: int
    """:class:`int`: The ID of the blessing."""
    name: str
    """:class:`str`: The name of the blessing."""
    max_level: int
    """:class:`int`: The level of the blessing."""
    icon_url: str = field(name="icon")
    """:class:`str`: The icon URL of the blessing."""
    summary: str = field(name="simple_desc")
    """:class:`str`: The summary of the blessing."""
    description: str = field(name="desc")
    """:class:`str`: The description of the blessing."""
    usage_description: str = field(name="desc_battle")
    """:class:`str`: The usage description of the blessing."""
    params: list[int | float]
    """:class:`list[Union[:class:`int`, :class:`float`]]`: The parameters of the blessing."""


class SRSSimUniverseCurio(MihomoBase, frozen=True):
    id: int
    """:class:`int`: The ID of the curio."""
    name: str
    """:class:`str`: The name of the curio."""
    icon_url: str = field(name="icon")
    """:class:`str`: The icon URL of the curio."""
    description: str = field(name="desc")
    """:class:`str`: The description of the curio."""
    story_description: str = field(name="story_desc")
    """:class:`str`: The story description of the curio."""
    params: list[int | float]
    """:class:`list[Union[:class:`int`, :class:`float`]]`: The parameters of the curio."""
