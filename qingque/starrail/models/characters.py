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

from qingque.mihomo.models.combats import ElementType, PathType, SkillEffectType, SkillUsageType

from .base import SRSBase
from .stats import SRSStatsIDValue, SRSStatsTypeValue

__all__ = (
    "SRSCharacter",
    "SRSCharacterSkill",
    "SRSCharacterSkillTrace",
    "SRSCharacterEidolon",
)


class SRSCharacterSkill(SRSBase, frozen=True):
    id: str
    """:class:`str`: The skill ID."""
    name: str
    """:class:`str`: The skill name."""
    max_level: int
    """:class:`int`: The skill max level."""
    type: SkillUsageType
    """:class:`SkillEffectType`: The skill type."""
    type_description: str = field(name="type_text")
    """:class:`str`: The skill type description."""
    effect: SkillEffectType
    """:class:`SkillEffectType`: The skill effect."""
    effect_description: str = field(name="effect_text")
    """:class:`str`: The skill effect description."""
    summary: str = field(name="simple_desc")
    """:class:`str`: The skill summary."""
    description: str = field(name="desc")
    """:class:`str`: The skill description."""
    icon_url: str = field(name="icon")
    """:class:`str`: The skill icon URL."""
    element: ElementType | None = field(default=None)
    """:class:`ElementType`: The skill element."""
    paramters: list[list[int | float]] = field(default_factory=list, name="params")
    """:class:`list[list[int | float]]`: The skill parameters."""


class SRSSkillTraceLevelUp(SRSBase, frozen=True):
    promotion: int
    """:class:`int`: The skill trace level up target."""
    properties: list[SRSStatsTypeValue] = field(default_factory=list)
    """:class:`list[SkillTraceProperties]`: The skill trace level up properties."""
    materials: list[SRSStatsIDValue] = field(default_factory=list)
    """:class:`list[SkillTraceIDValue]`: The skill trace level up materials."""


class SRSCharacterSkillTrace(SRSBase, frozen=True):
    id: str
    """:class:`str`: The skill trace ID."""
    name: str
    """:class:`str`: The skill trace name."""
    max_level: int
    """:class:`int`: The skill trace max level."""
    anchor_point: str = field(name="anchor")
    """:class:`str`: The skill trace anchor point or position."""
    icon_url: str = field(name="icon")
    """:class:`str`: The skill trace icon URL."""
    level_up_skills: list[SRSStatsIDValue] = field(default_factory=list, name="level_up_skills")
    """:class:`list[SkillTraceIDValue]`: The skill trace level up skills."""
    levels: list[SRSSkillTraceLevelUp] = field(default_factory=list)
    """:class:`list[SkillTraceLevelUp]`: The skill trace levels."""
    pre_point_ids: list[str] = field(default_factory=list, name="pre_points")
    """:class:`list[str]`: The skill trace pre points."""


class SRSCharacterEidolon(SRSBase, frozen=True):
    id: str
    """:class:`str`: The eidolon ID."""
    name: str
    """:class:`str`: The eidolon name."""
    rank: int
    """:class:`int`: The eidolon rank."""
    description: str = field(name="desc")
    """:class:`str`: The eidolon description."""
    icon_url: str = field(name="icon")
    """:class:`str`: The eidolon icon URL."""
    materials: list[SRSStatsIDValue] = field(default_factory=list)
    """:class:`list[SkillTraceIDValue]`: The eidolon materials needed to unlock."""
    level_up_skills: list[SRSStatsIDValue] = field(default_factory=list, name="level_up_skills")
    """:class:`list[SkillTraceIDValue]`: The eidolon level up skills."""


class SRSCharacter(SRSBase, frozen=True):
    id: str
    """:class:`str`: The character ID."""
    name: str
    """:class:`str`: The character name."""
    tag: str
    """:class:`str`: The character tag."""
    rarity: int
    """:class:`int`: The character rarity."""
    path: PathType
    """:class:`PathType`: The character path."""
    element: ElementType
    """:class:`ElementType`: The character element."""
    max_energy: int = field(name="max_sp")
    """:class:`int`: The character max energy."""
    icon_url: str = field(name="icon")
    """:class:`str`: The character icon URL."""
    preview_url: str = field(name="preview")
    """:class:`str`: The character preview URL."""
    portrait_url: str = field(name="portrait")
    """:class:`str`: The character portrait URL."""
    eidolon_ids: list[str] = field(default_factory=list, name="ranks")
    """:class:`list[str]`: The character eidolons."""
    skill_ids: list[str] = field(default_factory=list, name="skills")
    """:class:`list[str]`: The character skills."""
    trace_ids: list[str] = field(default_factory=list, name="skill_trees")
    """:class:`list[str]`: The character traces."""
