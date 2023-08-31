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

from enum import Enum

from msgspec import field

from .base import SRSBase
from .stats import SRSStatsTypeValue

__all__ = (
    "SRSRelicType",
    "SRSRelic",
    "SRSRelicSet",
    "SRSRelicStatsValue",
    "SRSRelicSubStatsValue",
    "SRSRelicStats",
    "SRSRelicSubStats",
)


class SRSRelicType(str, Enum):
    Head = "HEAD"
    Hand = "HAND"
    Body = "BODY"
    Foot = "FOOT"
    PlanarOrb = "NECK"
    PlanarRope = "OBJECT"

    @property
    def order(self) -> int:
        return {
            SRSRelicType.Head: 1,
            SRSRelicType.Hand: 2,
            SRSRelicType.Body: 3,
            SRSRelicType.Foot: 4,
            SRSRelicType.PlanarOrb: 5,
            SRSRelicType.PlanarRope: 6,
        }[self]


class SRSRelic(SRSBase, frozen=True):
    id: str
    """:class:`str`: The relic ID."""
    set_id: str
    """:class:`str`: The relic set ID."""
    name: str
    """:class:`str`: The relic name."""
    rarity: int
    """:class:`int`: The relic rarity."""
    type: SRSRelicType
    """:class:`SRSRelicType`: The relic type."""
    icon_url: str = field(name="icon")
    """:class:`str`: The relic icon URL."""


class SRSRelicSet(SRSBase, frozen=True):
    id: str
    """:class:`str`: The relic set ID."""
    name: str
    """:class:`str`: The relic set name."""
    icon_url: str = field(name="icon")
    """:class:`str`: The relic set icon URL.""" ""
    descriptions: list[str] = field(name="desc")
    """:class:`list[str]`: The relic set descriptions."""
    properties: list[list[SRSStatsTypeValue]]
    """:class:`list[list[SRSStatsTypeValue]]`: The relic set properties."""


class SRSRelicStatsValue(SRSBase, frozen=True):
    id: str = field(name="affix_id")
    """:class:`str`: The relic stats ID."""
    type: str = field(name="property")
    """:class:`str`: The relic stats type."""
    base: int | float = field(name="base")
    """:class:`int | float`: The relic stats base value."""
    step: int | float = field(name="step")
    """:class:`int | float`: The relic stats step value."""


class SRSRelicSubStatsValue(SRSRelicStatsValue, frozen=True):
    step_num: int = field(name="step_num")
    """:class:`int`: The relic sub stats step number."""


class SRSRelicStats(SRSBase, frozen=True):
    id: str
    """:class:`str`: The relic stats ID."""
    stats: dict[str, SRSRelicStatsValue] = field(name="affixes")
    """:class:`dict[str, SRSRelicStatsValue]`: The relic stats."""


class SRSRelicSubStats(SRSBase, frozen=True):
    id: str
    """:class:`str`: The relic sub stats ID."""
    stats: dict[str, SRSRelicSubStatsValue] = field(name="affixes")
    """:class:`dict[str, SRSRelicSubStatsValue]`: The relic sub stats."""
