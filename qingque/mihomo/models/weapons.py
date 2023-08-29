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
from .combats import Path
from .stats import StatsAtrributes, StatsProperties

__all__ = ("LightCone",)


class LightCone(MihomoBase, frozen=True):
    id: str
    """:class:`str`: The ID of the light cone."""
    name: str
    """:class:`str`: The name of the light cone."""
    rarity: int
    """:class:`int`: The rarity of the light cone."""
    level: int
    """:class:`int`: The level of the light cone."""
    ascension: int = field(name="promotion")
    """:class:`int`: The ascension level of the light cone."""
    superimpose: int = field(name="rank")
    """:class:`int`: The superimpose level of the light cone."""
    icon_url: str = field(name="icon")
    """:class:`str`: The icon URL of the light cone."""
    preview_url: str = field(name="preview")
    """:class:`str`: The preview image URL of the light cone."""
    portrait_url: str = field(name="portrait")
    """:class:`str`: The portrait image URL of the light cone."""
    path: Path
    """:class:`Path`: The path of the light cone."""
    attributes: list[StatsAtrributes]
    """:class:`list[StatsAtrributes]`: The base attributes of the light cone."""
    properties: list[StatsProperties]
    """:class:`list[StatsProperties]`: The additional attributes that the light cone gives."""
