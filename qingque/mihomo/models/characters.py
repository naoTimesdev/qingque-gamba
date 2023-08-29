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
from .combats import Element, Path, Skill, SkillTrace
from .relics import Relic, RelicSet
from .stats import StatsAtrributes, StatsProperties
from .weapons import LightCone

__all__ = ("Character",)


class Character(MihomoBase, frozen=True):
    id: str
    """:class:`str`: The ID of the character."""
    name: str
    """:class:`str`: The name of the character."""
    rarity: int
    """:class:`int`: The rarity of the character."""
    level: int
    """:class:`int`: The level of the character."""
    light_cone: LightCone | None
    """:class:`LightCone`: The used light cone for the character."""
    relics: list[Relic]
    """:class:`list[Relic]`: The relics used on the character."""
    relic_sets: list[RelicSet]
    """:class:`list[RelicSet]`: The bonus stats from relic sets used on the character."""
    attributes: list[StatsAtrributes]
    """:class:`list[StatsAtrributes]`: The base attributes of the character."""
    additions: list[StatsAtrributes]
    """:class:`list[StatsAtrributes]`: The additional attributes that the character got from relics and others."""
    properties: list[StatsProperties]
    """:class:`list[StatsProperties]`: The properties of the character."""
    path: Path
    """:class:`Path`: The path of the character."""
    element: Element
    """:class:`Element`: The element of the character."""
    skills: list[Skill]
    """:class:`list[Skill]`: The skills of the character."""
    traces: list[SkillTrace] = field(name="skill_trees")
    """:class:`list[SkillTrace]`: The skill traces of the character."""
    eidolon: int = field(name="rank")
    """:class:`int`: The eidolon level of the character."""
    ascension: int = field(name="promotion")
    """:class:`int`: The ascension level of the character."""
    icon_url: str = field(name="icon")
    """:class:`str`: The icon URL of the character."""
    preview_url: str = field(name="preview")
    """:class:`str`: The preview image URL of the character."""
    portrait_url: str = field(name="portrait")
    """:class:`str`: The portrait image URL of the character."""
    eidolon_icons: list[str] = field(name="rank_icons")
    """:class:`list[str]`: The eidolon icons URL of the character."""
