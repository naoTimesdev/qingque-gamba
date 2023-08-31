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

from qingque.mihomo.models.combats import ElementType, PathType
from qingque.mihomo.models.stats import StatsField

from .base import SRSBase

__all__ = (
    "SRSElement",
    "SRSPath",
    "SRSProperties",
    "SRSStatsIDValue",
    "SRSStatsTypeValue",
    "SRSPromotion",
)


class SRSElement(SRSBase, frozen=True):
    id: ElementType
    """:class:`ElementType`: The element ID."""
    name: str
    """:class:`str`: The element name."""
    description: str = field(name="desc")
    """:class:`str`: The element description."""
    color: str
    """:class:`str`: The element color."""
    icon_url: str = field(name="icon")
    """:class:`str`: The element icon URL."""


class SRSPath(SRSBase, frozen=True):
    id: PathType
    """:class:`PathType`: The path ID."""
    name: str
    """:class:`str`: The path name."""
    description: str = field(name="desc")
    """:class:`str`: The path description."""
    icon_url: str = field(name="icon")
    """:class:`str`: The path icon URL."""


class SRSProperties(SRSBase, frozen=True):
    order: int
    """:class:`int`: The properties order."""
    type: str
    """:class:`str`: The properties type."""
    name: str
    """:class:`str`: The properties name."""
    kind: StatsField = field(name="field")
    """:class:`StatsField`: The properties field."""
    icon_url: str = field(name="icon")
    """:class:`str`: The properties icon URL."""
    is_ratio: bool = field(name="ratio")
    """:class:`bool`: The properties is a ratio."""
    is_percentage: bool = field(name="percent")
    """:class:`bool`: The properties is a percentage."""
    is_substats: bool = field(name="affix")
    """:class:`bool`: The properties is a sub stats value."""


class SRSStatsTypeValue(SRSBase, frozen=True):
    type: str
    """:class:`str`: The skill trace property type."""
    value: int | float
    """:class:`float`: The skill trace property value."""


class SRSStatsIDValue(SRSBase, frozen=True):
    id: str
    """:class:`str`: The skill trace ID value."""
    amount: int = field(name="num")
    """:class:`int`: The skill trace amount value."""


class SRSPromotionValue(SRSBase, frozen=True):
    base: int | float
    """:class:`int | float`: The promotion value base."""
    step: int | float
    """:class:`int | float`: The promotion value step."""


class SRSPromotion(SRSBase, frozen=True):
    id: str
    """:class:`str`: The promotion ID."""
    materials: list[list[SRSStatsIDValue]] = field(default_factory=list)
    """:class:`list[list[SkillTraceIDValue]]`: The promotion materials."""
    values: list[dict[str, SRSPromotionValue]] = field(default_factory=list)
    """:class:`list[dict[str, PromotionValue]]`: The promotion values."""
