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

from msgspec import Struct, field

from .common import HYElementType

__all__ = (
    "ChronicleRelicType",
    "ChronicleCharacterLightCone",
    "ChronicleCharacterRelic",
    "ChronicleCharacterEidolon",
    "ChronicleCharacter",
    "ChronicleCharacters",
)


class ChronicleRelicType(int, Enum):
    Head = 1
    Hand = 2
    Body = 3
    Foot = 4
    PlanarOrb = 5
    PlanarRope = 6


class ChronicleCharacterLightCone(Struct):
    id: int
    """:class:`int`: The ID of the light cone."""
    name: str
    """:class:`str`: The name of the light cone."""
    icon_url: str = field(name="icon")
    """:class:`str`: The icon URL of the light cone."""
    level: int = field(default=1)
    """:class:`int`: The level of the light cone."""
    description: str = field(name="desc", default="")
    """:class:`str`: The description of the light cone."""
    superimpose: int = field(default=1, name="rank")
    """:class:`int`: The superimpose level of the light cone."""

    @property
    def icon_path(self) -> str:
        """:class:`str`: The path of the light cone icon (local/SRS)."""
        return f"icon/light_cone/{self.id}.png"

    @property
    def preview_url(self) -> str:
        """:class:`str`: The URL of the light cone's preview image."""
        return f"image/light_cone_preview/{self.id}.png"

    @property
    def portrait_url(self) -> str:
        """:class:`str`: The URL of the light cone portrait image."""
        return f"image/light_cone_portrait/{self.id}.png"


class ChronicleCharacterRelic(Struct):
    id: int
    """:class:`int`: The ID of the relic."""
    name: str
    """:class:`str`: The name of the relic."""
    type: ChronicleRelicType = field(name="pos")
    """:class:`ChronicleRelicType`: The type of the relic."""
    rarity: int
    """:class:`int`: The rarity of the relic."""
    icon_url: str = field(name="icon")
    """:class:`str`: The icon URL of the relic."""
    level: int = field(default=1)
    """:class:`int`: The level of the relic."""
    description: str = field(name="desc", default="")
    """:class:`str`: The description of the relic."""


class ChronicleCharacterEidolon(Struct):
    id: int
    """:class:`int`: The ID of the eidolon."""
    name: str
    """:class:`str`: The name of the eidolon."""
    icon_url: str = field(name="icon")
    """:class:`str`: The icon URL of the eidolon."""
    order: int = field(name="pos")
    """:class:`int`: The order of the eidolon."""
    description: str = field(name="desc", default="")
    """:class:`str`: The description of the eidolon."""
    unlocked: bool = field(default=False, name="is_unlocked")
    """:class:`bool`: Whether the eidolon is unlocked or not."""


class ChronicleCharacter(Struct):
    id: int
    """:class:`int`: The ID of the character."""
    name: str
    """:class:`str`: The name of the character."""
    level: int
    """:class:`int`: The level of the character."""
    icon_url: str = field(name="icon")
    """:class:`str`: The URL of the character's icon."""
    rarity: int
    """:class:`int`: The rarity of the character."""
    eidolon: int = field(name="rank")
    """:class:`int`: The total of activated eidolon of a character."""
    element: HYElementType
    """:class:`HYElementType`: The element of the character."""
    ligh_cone: ChronicleCharacterLightCone | None = field(name="equip", default=None)
    """:class:`ChronicleCharacterLightCone | None`: The light cone of the character."""
    relics: list[ChronicleCharacterRelic] = field(default_factory=list)
    """:class:`list[ChronicleCharacterRelic]`: The list of relics of the character."""
    planar_relics: list[ChronicleCharacterRelic] = field(default_factory=list, name="ornaments")
    """:class:`list[ChronicleCharacterRelic]`: The list of planar relics of the character."""
    eidolons: list[ChronicleCharacterEidolon] = field(default_factory=list, name="ranks")


class ChronicleCharacters(Struct):
    characters: list[ChronicleCharacter] = field(name="avatar_list")
    """:class:`list[ChronicleCharacter]`: The list of characters."""
