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

from qingque.hylab.constants import SERVER_TO_STARRAIL_REGION

from .common import ChronicleDate, HYElementType

__all__ = (
    "RogueBlessingType",
    "ChronicleRogueOverview",
    "ChronicleRoguePeriodOverview",
    "ChronicleRogueCurio",
    "ChronicleRogueBlessingKind",
    "ChronicleRogueBlessingItem",
    "ChronicleRogueBlessing",
    "ChronicleRogueCharacter",
    "ChronicleRoguePeriodRun",
    "ChronicleRoguePeriod",
    "ChronicleSimulatedUniverse",
)


class RogueBlessingType(int, Enum):
    Preservation = 120
    """Preservation/Knight"""
    Remembrance = 121
    """Remembrance/Memory"""
    Nihility = 122
    """Nihility/Warlock"""
    Abundance = 123
    """Abundance/Priest"""
    Hunt = 124
    """Hunt/Rogue"""
    Destruction = 125
    """Destruction/Warrior"""
    Elation = 126
    """Elation/Joy"""
    Propagation = 127
    """Propagation"""
    # Explore/Trailblazer/Akivili: ???

    @property
    def icon_url(self):
        match self:
            case RogueBlessingType.Remembrance:
                return "icon/path/Memory.png"
            case RogueBlessingType.Elation:
                return "icon/path/Joy.png"
            case RogueBlessingType.Propagation:
                return "icon/path/None.png"
            case _:
                return f"icon/path/{self.name}.png"


class ChronicleRogueOverview(Struct):
    unlocked_blessings: int = field(name="unlocked_buff_num")
    """:class:`int`: The number of unlocked blessings."""
    unlocked_curios: int = field(name="unlocked_miracle_num")
    """:class:`int`: The number of unlocked curios."""
    unlocked_skills: int = field(name="unlocked_skill_points")
    """:class:`int`: The number of unlocked skills."""


class ChronicleRoguePeriodOverview(Struct):
    id: int
    """:class:`int`: The ID of the run (Most likely simple counting)."""
    total_run: int = field(name="finish_cnt")
    """:class:`int`: The total successful run in the current period for Simulated Universe."""
    start_time: ChronicleDate = field(name="schedule_begin")
    """:class:`ChronicleDate`: The start time of the SU period."""
    end_time: ChronicleDate = field(name="schedule_end")
    """:class:`ChronicleDate`: The end time of the SU period."""
    score: int = field(name="current_rogue_score")
    """:class:`int`: The current score of the period."""
    max_score: int = field(name="max_rogue_score")
    """:class:`int`: The maximum score of the period."""


class ChronicleRogueCurio(Struct):
    id: int
    """:class:`int`: The ID of the curio."""
    name: str
    """:class:`str`: The name of the curio."""
    icon_url: str = field(name="icon")
    """:class:`str`: The URL of the icon of the curio."""


class ChronicleRogueBlessingKind(Struct):
    id: int
    """:class:`int`: The ID of the blessing kind."""
    name: str
    """:class:`str`: The name of the blessing kind."""
    count: int = field(name="cnt")
    """:class:`int`: The number of blessings of the kind."""

    @property
    def type(self) -> RogueBlessingType:
        return RogueBlessingType(self.id)


class ChronicleRogueBlessingItem(Struct):
    id: int
    """:class:`int`: The ID of the blessing."""
    name: str
    """:class:`str`: The name of the blessing."""
    rank: int
    """:class:`int`: The rank of the blessing."""
    enhanced: bool = field(name="is_evoluted")
    """:class:`bool`: Whether the blessing is enhanced or not."""


class ChronicleRogueBlessing(Struct):
    kind: ChronicleRogueBlessingKind = field(name="base_type")
    """:class:`ChronicleRogueBlessingKind`: The kind of the blessing."""
    items: list[ChronicleRogueBlessingItem]
    """:class:`list[ChronicleRogueBlessingItem]`: The list of blessings."""


class ChronicleRogueCharacter(Struct):
    id: int
    """:class:`int`: The ID of the character."""
    level: int
    """:class:`int`: The level of the character."""
    rarity: int
    """:class:`int`: The rarity of the character."""
    icon_url: str = field(name="icon")
    """:class:`str`: The URL of the icon of the character."""
    eidolons: int = field(name="rank")
    """:class:`int`: The number of activated eidolons of the character."""
    element: HYElementType
    """:class:`HYElementType`: The element of the character."""


class ChronicleRoguePeriodRun(Struct):
    id: int = field(name="progress")
    """:class:`int`: The ID of the world."""
    name: str
    """:class:`str`: The name of the world."""
    end_time: ChronicleDate = field(name="finish_time")
    """:class:`ChronicleDate`: The end time of the run."""
    score: int
    """:class:`int`: The final score of the run."""
    difficulty: int
    """:class:`int`: The difficulty of the run."""
    blessings: list[ChronicleRogueBlessing] = field(name="buffs")
    """:class:`list[ChronicleRogueBlessing]`: The list of blessings."""
    blessing_kinds: list[ChronicleRogueBlessingKind] = field(name="base_type_list")
    """:class:`list[ChronicleRogueBlessingKind]`: The list of blessing kinds."""
    curios: list[ChronicleRogueCurio] = field(name="miracles")
    """:class:`list[ChronicleRogueCurio]`: The list of curios."""
    final_lineups: list[ChronicleRogueCharacter] = field(name="final_lineup")
    """:class:`list[ChronicleRogueCharacter]`: The list of final lineups."""

    @property
    def icon_url(self):
        return f"icon/rogue/worlds/PlanetM{self.id}.png"


class ChronicleRoguePeriod(Struct):
    has_data: bool
    """:class:`bool`: Whether the record has data or not."""
    overview: ChronicleRoguePeriodOverview = field(name="basic")
    """:class:`ChronicleRoguePeriodOverview`: The overview of the period record."""
    records: list[ChronicleRoguePeriodRun]
    """:class:`list[ChronicleRoguePeriodRun]`: The list of runs in the period."""
    best_record: ChronicleRoguePeriodRun
    """:class:`ChronicleRoguePeriodRun`: The best run in the period."""


class ChronicleRogueUserInfo(Struct):
    name: str = field(name="nickname")
    """:class:`str`: The name of the user."""
    server: str
    """:class:`str`: The server of the user."""
    level: int
    """:class:`int`: The level of the user."""

    @property
    def region(self):
        """:class:`str`: The region of the user."""
        return SERVER_TO_STARRAIL_REGION[self.server]


class ChronicleSimulatedUniverse(Struct):
    user: ChronicleRogueUserInfo = field(name="role")
    """:class:`ChronicleRogueUserInfo`: The user info."""
    overview: ChronicleRogueOverview = field(name="basic_info")
    """:class:`ChronicleRogueOverview`: The overview of the user."""
    current: ChronicleRoguePeriod = field(name="current_record")
    """:class:`ChronicleRoguePeriod`: The current period."""
    previous: ChronicleRoguePeriod = field(name="last_record")
    """:class:`ChronicleRoguePeriod`: The previous period."""
