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

__all__ = (
    "HYElementType",
    "ChronicleOverviewStats",
    "ChronicleOverviewCharacter",
    "ChronicleOverview",
)


class HYElementType(str, Enum):
    Physical = "physical"
    Fire = "fire"
    Ice = "ice"
    Lightning = "lightning"
    Wind = "wind"
    Quantum = "quantum"
    Imaginary = "imaginary"

    Unknown = ""


class ChronicleOverviewStats(Struct):
    active: int = field(name="active_days", default=1)
    """:class:`int`: The number of active days."""
    avatar_count: int = field(name="avatar_num", default=1)
    """:class:`int`: The number of avatars."""
    achievements: int = field(name="achievement_num", default=0)
    """:class:`int`: The number of achievements."""
    chests: int = field(name="chest_num", default=0)
    """:class:`int`: The number of opened chests/treasures."""
    moc_floor: str | None = field(name="abyss_process", default=None)
    """:class:`str | None`: The current floor of Memory of Chaos."""

    # There is also field_ext_map, but I'll ignore it.


class ChronicleOverviewCharacter(Struct):
    id: int
    """:class:`int`: The ID of the character."""
    name: str
    """:class:`str`: The name of the character."""
    icon_url: str = field(name="icon")
    """:class:`str`: The URL of the character's icon."""
    rarity: int
    """:class:`int`: The rarity of the character."""
    eidolon: int = field(name="rank")
    """:class:`int`: The total of activated eidolon of a character."""
    element: HYElementType
    """:class:`HYElementType`: The element of the character."""
    chosen: bool = field(name="is_chosen")
    """:class:`bool`: Whether the character is currently are being deployed in-game."""

    @property
    def icon_path(self):
        """:class:`str`: The path of the character's icon (local/SRS)."""
        return f"icon/avatar/{self.id}.png"

    @property
    def preview_url(self):
        """:class:`str`: The URL of the character's preview image."""
        return f"image/character_preview/{self.id}.png"

    @property
    def portrait_url(self):
        """:class:`str`: The URL of the character's portrait image."""
        return f"image/character_portrait/{self.id}.png"


class ChronicleOverview(Struct):
    stats: ChronicleOverviewStats
    """:class:`ChronicleOverviewStats`: The stats of the user."""
    characters: list[ChronicleOverviewCharacter] = field(name="avatar_list")
    """:class:`list[ChronicleOverviewCharacter]`: The list of characters."""
    avatar_url: str = field(name="cur_head_icon_url")
    """:class:`str`: The URL of the user's avatar."""
    phone_background_url: str = field(name="phone_background_image_url")
    """:class:`str`: The URL of the user's phone background."""
