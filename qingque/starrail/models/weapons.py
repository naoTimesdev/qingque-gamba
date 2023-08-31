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

from qingque.mihomo.models.combats import PathType
from qingque.starrail.models.stats import SRSStatsTypeValue

from .base import SRSBase

__all__ = (
    "SRSLightCone",
    "SRSLightConeSuperimpose",
)


class SRSLightConeSuperimpose(SRSBase, frozen=True):
    id: str
    """:class:`str`: The light cone superimpose ID."""
    skill: str
    """:class:`str`: The light cone superimpose skill name."""
    description: str = field(name="desc")
    """:class:`str`: The light cone superimpose skill description."""
    parameters: list[list[int | float]] = field(name="params")
    """:class:`list[list[int | float]]`: The light cone superimpose skill parameters."""
    properties: list[list[SRSStatsTypeValue]]
    """:class:`list[list[SRSStatsTypeValue]]`: The light cone superimpose skill properties."""


class SRSLightCone(SRSBase, frozen=True):
    id: str
    """:class:`str`: The light cone ID."""
    name: str
    """:class:`str`: The light cone name."""
    rarity: int
    """:class:`int`: The light cone rarity."""
    path: PathType
    """:class:`PathType`: The light cone path."""
    description: str = field(name="desc")
    """:class:`str`: The light cone description."""
    icon_url: str = field(name="icon")
    """:class:`str`: The light cone icon URL."""
    preview_url: str = field(name="preview")
    """:class:`str`: The light cone preview URL."""
    portrait_url: str = field(name="portrait")
    """:class:`str`: The light cone portrait URL."""
