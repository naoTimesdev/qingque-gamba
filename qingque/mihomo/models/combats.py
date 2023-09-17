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

from .base import MihomoBase

__all__ = (
    "ElementType",
    "PathType",
    "SkillUsageType",
    "SkillEffectType",
    "Path",
    "Element",
    "Skill",
    "SkillTrace",
)


class ElementType(str, Enum):
    Physical = "Physical"
    Fire = "Fire"
    Ice = "Ice"
    Lightning = "Thunder"
    Wind = "Wind"
    Quantum = "Quantum"
    Imaginary = "Imaginary"

    # Alias
    Thunder = "Lightning"

    Unknown = ""

    @property
    def icon_url(self) -> str:
        match self:
            case ElementType.Lightning | ElementType.Thunder:
                return "icon/element/Lightning.png"
            case _:
                return f"icon/element/{self.name}.png"


class PathType(str, Enum):
    Destruction = "Warrior"
    Hunt = "Rogue"
    Erudition = "Mage"
    Harmony = "Shaman"
    Nihility = "Warlock"
    Preservation = "Knight"
    Abundance = "Priest"
    General = "Unknown"


class SkillUsageType(str, Enum):
    Basic = "Normal"
    """A basic attack."""
    Skill = "BPSkill"
    """A skill that can be used in battle."""
    Ultimate = "Ultra"
    """An ultimate skill that can be used in battle."""
    Talent = "Talent"
    """Character's talent that used in combat."""
    Technique = "Maze"
    """Overworld technique that can be used outside of combat."""
    TechniqueAttack = "MazeNormal"
    """Overworld technique that can be used outside of combat as an attack."""

    @property
    def order(self) -> int:
        return {
            SkillUsageType.Basic: 1,
            SkillUsageType.Skill: 2,
            SkillUsageType.Ultimate: 3,
            SkillUsageType.Talent: 4,
            SkillUsageType.Technique: 5,
            SkillUsageType.TechniqueAttack: 6,
        }[self]


class SkillEffectType(str, Enum):
    Attack = "SingleAttack"
    """A single target attack."""
    OverworldAttack = "MazeAttack"
    """An attack started from the overworld area."""
    MultiAttack = "Blast"
    """Multi-target/adjacent attack."""
    AoEAttack = "AoEAttack"
    """Multi-target/all-out attack."""
    Bounce = "Bounce"
    """A skill that bounces from selected enemy to another randomly."""
    Buff = "Enhance"
    """Enhancing or boosting allies"""
    Debuff = "Impair"
    """Debuffing or weakening enemies"""
    Defence = "Defence"
    """Defending allies from incoming attacks, usually give a shield."""
    Restore = "Restore"
    """Restoring allies health, overall skill points or something similar."""
    Passive = "Support"
    """A passive skill that active for x amount of turns sometimes."""


class Element(MihomoBase, frozen=True):
    id: ElementType
    """:class:`ElementType`: The element ID."""
    name: str
    """:class:`str`: The element name."""
    color: str
    """:class:`str`: The element color."""
    icon_url: str = field(name="icon")
    """:class:`str`: The element icon URL."""


class Path(MihomoBase, frozen=True):
    id: PathType
    """:class:`PathType`: The path ID."""
    name: str
    """:class:`str`: The path name."""
    icon_url: str = field(name="icon")
    """:class:`str`: The path icon URL."""


class Skill(MihomoBase, frozen=True):
    id: str
    """:class:`str`: The skill ID."""
    name: str
    """:class:`str`: The skill name."""
    level: int
    """:class:`int`: The skill level."""
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
    element: Element | None = field(default=None)
    """:class:`SkillElement`: The skill element."""


class SkillTrace(MihomoBase, frozen=True):
    id: str
    """:class:`str`: The skill trace ID."""
    level: int
    """:class:`int`: The skill trace level."""
    max_level: int
    """:class:`int`: The skill trace max level."""
    anchor_point: str = field(name="anchor")
    """:class:`str`: The skill trace anchor point or position."""
    icon_url: str = field(name="icon")
    """:class:`str`: The skill trace icon URL."""
    parent_id: str | None = field(name="parent", default=None)
    """:class:`str`: The skill trace parent ID, if exist it means it is a branch."""
