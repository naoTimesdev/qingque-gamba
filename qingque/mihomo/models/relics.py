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
from .stats import StatsProperties, StatsPropertiesAffix

__all__ = (
    "Relic",
    "RelicSet",
)


class Relic(MihomoBase, frozen=True):
    id: str
    """:class:`str`: The ID of the relic."""
    name: str
    """:class:`str`: The name of the relic."""
    set_id: str
    """:class:`str`: The ID of the relic set."""
    set_name: str
    """:class:`str`: The name of the relic set."""
    rarity: int
    """:class:`int`: The rarity of the relic."""
    level: int
    """:class:`int`: The level of the relic."""
    icon_url: str = field(name="icon")
    """:class:`str`: The icon URL of the relic."""
    main_stats: StatsProperties = field(name="main_affix")
    """:class:`StatsProperties`: The main stats of the relic."""
    sub_stats: list[StatsPropertiesAffix] = field(name="sub_affix")
    """:class:`list[StatsPropertiesAffix]`: The sub stats of the relic."""


class RelicSet(MihomoBase, frozen=True):
    """The active relic sets bonus"""

    id: str
    """:class:`str`: The ID of the relic set."""
    name: str
    """:class:`str`: The name of the relic set."""
    icon_url: str = field(name="icon")
    """:class:`str`: The icon URL of the relic set."""
    need: int = field(name="num")
    """:class:`int`: The total number of needed relics for the set bonus."""
    description: str = field(name="desc")
    """:class:`str`: The description of the relic set bonus."""
    properties: list[StatsProperties]
    """:class:`list[StatsProperties]`: The properties of the relic set bonus."""
