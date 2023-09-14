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

from msgspec import Struct, field

from .common import ChronicleDate, HYElementType

__all__ = (
    "ChronicleFHCharacter",
    "ChronicleFHNode",
    "ChronicleFHFloor",
    "ChronicleForgottenHall",
)


class ChronicleFHCharacter(Struct):
    id: int
    """:class:`int`: The ID of the character."""
    icon_url: str = field(name="icon")
    """:class:`str`: The URL of the character's icon."""
    rarity: int
    """:class:`int`: The rarity of the character."""
    level: int
    """:class:`int`: The level of the character."""
    eidolon: int = field(name="rank")
    """:class:`int`: The total of activated eidolon of a character."""
    element: HYElementType
    """:class:`HYElementType`: The element of the character."""

    @property
    def icon_path(self) -> str:
        """:class:`str`: The path of the character's icon (local/SRS)."""
        return f"icon/avatar/{self.id}.png"

    @property
    def preview_url(self) -> str:
        """:class:`str`: The URL of the character's preview image."""
        return f"image/character_preview/{self.id}.png"

    @property
    def portrait_url(self) -> str:
        """:class:`str`: The URL of the character's portrait image."""
        return f"image/character_portrait/{self.id}.png"


class ChronicleFHNode(Struct):
    challenge_time: ChronicleDate
    """:class:`ChronicleFHDate`: The challenge time of the node."""
    characters: list[ChronicleFHCharacter] = field(name="avatars")
    """:class:`list[ChronicleMoCCharacter]`: The list of characters used for the node."""


class ChronicleFHFloor(Struct):
    name: str
    """:class:`str`: The name of the floor."""
    is_chaos: bool
    """:class:`bool`: Whether the floor is forgotten hall or not."""
    round_total: int = field(name="round_num")
    """:class:`int`: The number of rounds used for the floor."""
    stars_total: int = field(name="star_num")
    """:class:`int`: The number of stars obtained for the floor."""
    node_1: ChronicleFHNode
    """:class:`ChronicleFHNode`: The first node of the floor."""
    node_2: ChronicleFHNode
    """:class:`ChronicleFHNode`: The second node of the floor."""


class ChronicleForgottenHall(Struct):
    id: int = field(name="schedule_id")
    """:class:`int`: The ID of the forgotten hall."""
    start_time: ChronicleDate = field(name="begin_time")
    """:class:`ChronicleFHDate`: The start time of the forgotten hall."""
    end_time: ChronicleDate = field(name="end_time")
    """:class:`ChronicleFHDate`: The end time of the forgotten hall."""
    total_stars: int = field(name="star_num")
    """:class:`int`: The total stars of the forgotten hall."""
    max_floor: str
    """:class:`str`: The maximum floor finished for the forgotten hall."""
    total_battles: int = field(name="battle_num")
    """:class:`int`: The total battles conducted for this forgotten hall."""
    has_data: bool
    """:class:`bool`: Whether the forgotten hall has data or not."""
    floors: list[ChronicleFHFloor] = field(name="all_floor_detail")
    """:class:`list[ChroniclesFHFloor]`: The list of floors for the forgotten hall."""
