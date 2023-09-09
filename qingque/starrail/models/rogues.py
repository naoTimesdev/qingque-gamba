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

from qingque.mihomo.models.combats import ElementType

from .base import SRSBase

__all__ = (
    "SRSRogueBlessing",
    "SRSRogueBlessingType",
    "SRSRogueCurio",
    "SRSRogueWorld",
    "SRSRogueDLCBlock",
)


class SRSRogueWorld(SRSBase, frozen=True):
    id: int
    """:class:`int`: The world ID"""
    area_id: int
    """:class:`int`: The area progress ID (world numbering)"""
    name: str
    """:class:`str`: The world name"""
    icon_url: str = field(name="icon")
    """:class:`str`: The world icon URL (local)"""
    difficulty: int
    """:class:`int`: The world difficulty"""
    recommend_level: int
    """:class:`int`: The world recommended level"""
    score_map: dict[str, int]
    """:class:`dict[str, int]`: The world score map, basically how many points you will get for each stages stop."""
    weakness: list[ElementType]
    """:class:`list[ElementType]`: The world boss weakness."""

    @property
    def stages(self) -> list[int]:
        """:class:`list[int]`: The world stages/map/area."""
        return sorted(list(map(int, self.score_map.keys())))

    def get_stage(self, scores: int) -> int:
        """:class:`int`: Get the stage number from the scores."""
        for stage, score in self.score_map.items():
            if score == scores:
                return int(stage)
        raise ValueError(f"Invalid score: {scores}")


class SRSRogueCurio(SRSBase, frozen=True):
    id: int
    """:class:`int`: The curio ID"""
    name: str
    """:class:`str`: The curio name"""
    icon_url: str = field(name="icon")
    """:class:`str`: The curio icon URL (local)"""
    description: str = field(name="desc")
    """:class:`str`: The curio description"""
    params: list[int | float]
    """:class:`list[int | float]`: The curio description parameters"""
    story_description: str = field(name="story_desc")
    """:class:`str`: The curio story description"""


class SRSRogueBlessing(SRSBase, frozen=True):
    id: int
    """:class:`int`: The blessing ID"""
    name: str
    """:class:`str`: The blessing name"""
    icon_url: str = field(name="icon")
    """:class:`str`: The blessing icon URL (local)"""
    description: str = field(name="desc")
    """:class:`str`: The blessing description"""
    params: list[int | float]
    """:class:`list[int | float]`: The blessing description parameters"""
    summary: str = field(name="simple_desc")
    """:class:`str`: The blessing summary"""
    usage_description: str = field(name="desc_battle")
    """:class:`str`: The blessing usage description"""
    max_level: int
    """:class:`int`: The blessing max level"""


class SRSRogueBlessingType(SRSBase, frozen=True):
    id: int
    """:class:`int`: The blessing type ID"""
    name: str
    """:class:`str`: The blessing type name"""
    icon_url: str = field(name="icon")
    """:class:`str`: The blessing type icon URL (local)"""
    hint: str
    """:class:`str`: The blessing type hint"""


class SRSRogueDLCBlock(SRSBase, frozen=True):
    id: int
    """:class:`int`: The block ID"""
    name: str
    """:class:`str`: The block name"""
    icon_url: str = field(name="icon")
    """:class:`str`: The block icon URL (local)"""
