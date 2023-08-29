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
from .characters import Character

__all__ = (
    "ForgottenHallFloor",
    "MemoryOfChaosFloor",
    "SimulatedUniverse",
    "PlayerAvatar",
    "PlayerForgottenHall",
    "PlayerProgression",
    "PlayerInfo",
    "Player",
)


class ForgottenHallFloor(int, Enum):
    Unknown = 0
    """Unknown floor."""
    Belobog1 = 1
    """The Last Vestiges of Towering Citadel: Stage 1"""
    Belobog2 = 2
    """The Last Vestiges of Towering Citadel: Stage 2"""
    Belobog3 = 3
    """The Last Vestiges of Towering Citadel: Stage 3"""
    Belobog4 = 4
    """The Last Vestiges of Towering Citadel: Stage 4"""
    Belobog5 = 5
    """The Last Vestiges of Towering Citadel: Stage 5"""
    Belobog6 = 6
    """The Last Vestiges of Towering Citadel: Stage 6"""
    Belobog7 = 7
    """The Last Vestiges of Towering Citadel: Stage 7"""
    Belobog8 = 8
    """The Last Vestiges of Towering Citadel: Stage 8"""
    Belobog9 = 9
    """The Last Vestiges of Towering Citadel: Stage 9"""
    Belobog10 = 10
    """The Last Vestiges of Towering Citadel: Stage 10"""
    Belobog11 = 11
    """The Last Vestiges of Towering Citadel: Stage 11"""
    Belobog12 = 12
    """The Last Vestiges of Towering Citadel: Stage 12"""
    Belobog13 = 13
    """The Last Vestiges of Towering Citadel: Stage 13"""
    Belobog14 = 14
    """The Last Vestiges of Towering Citadel: Stage 14"""
    Belobog15 = 15
    """The Last Vestiges of Towering Citadel: Stage 15"""
    Xianzhou1 = 16
    """The Voyage of Navis Astriger: Stage 1"""
    Xianzhou2 = 17
    """The Voyage of Navis Astriger: Stage 2"""
    Xianzhou3 = 18
    """The Voyage of Navis Astriger: Stage 3"""
    Xianzhou4 = 19
    """The Voyage of Navis Astriger: Stage 4"""
    Xianzhou5 = 20
    """The Voyage of Navis Astriger: Stage 5"""
    Xianzhou6 = 21
    """The Voyage of Navis Astriger: Stage 6"""


class MemoryOfChaosFloor(int, Enum):
    Unknown = 0
    """Unknown floor."""
    Stage1 = 1
    """Memory of Chaos: Stage 1"""
    Stage2 = 2
    """Memory of Chaos: Stage 2"""
    Stage3 = 3
    """Memory of Chaos: Stage 3"""
    Stage4 = 4
    """Memory of Chaos: Stage 4"""
    Stage5 = 5
    """Memory of Chaos: Stage 5"""
    Stage6 = 6
    """Memory of Chaos: Stage 6"""
    Stage7 = 7
    """Memory of Chaos: Stage 7"""
    Stage8 = 8
    """Memory of Chaos: Stage 8"""
    Stage9 = 9
    """Memory of Chaos: Stage 9"""
    Stage10 = 10
    """Memory of Chaos: Stage 10"""


class SimulatedUniverse(int, Enum):
    Unknown = 0
    """Unknown universe."""
    HertaWorld = 1
    """World 1: Boss Enemy from Herta Space Station"""
    BelobogWorld = 2
    """World 2: Boss Enemy from Belobog/Jarilo-VI"""
    GepardWorld = 3
    """World 3: Gepard (Belobog Overworld) as Boss Enemy"""
    SvarogWorld = 4
    """World 4: Svarog (Belobog Underground) as Boss Enemy"""
    KafkaWorld = 5
    """World 5: Kafka (Stellaron Hunter) as Boss Enemy"""
    CocoliaWorld = 6
    """World 6: Cocolia (Belobog Finale) as Boss Enemy"""
    EbonDeerWorld = 7
    """World 7: Abundant Ebon Deer (Xianzhou) as Boss Enemy"""


class PlayerAvatar(MihomoBase, frozen=True):
    id: str
    """:class:`str`: The ID of the avatar."""
    name: str
    """:class:`str`: The name of the avatar."""
    icon_url: str = field(name="icon")
    """:class:`str`: The icon path of the avatar."""


class PlayerForgottenHall(MihomoBase, frozen=True):
    finished_floor: ForgottenHallFloor = field(name="pre_maze_group_index")
    """:class:`ForgottenHallFloor`: The finished floor index of the Forgotten Hall."""
    moc_finished_floor: MemoryOfChaosFloor = field(name="maze_group_index")
    """:class:`MemoryOfChaosFloor`: The finished floor index of the Memory of Chaos."""
    moc_floor_id: int = field(name="maze_group_id")
    """:class:`int`: The floor ID of the Memory of Chaos."""


class PlayerProgression(MihomoBase, frozen=True):
    forgotten_hall: PlayerForgottenHall = field(name="challenge_data")
    """:class:`PlayerForgottenHall`: The player's Forgotten Hall progression."""
    simulated_universe: SimulatedUniverse = field(name="pass_area_progress")
    """:class:`SimulatedUniverse`: The player's Simulated Universe progression."""
    light_cones: int = field(name="light_cone_count")
    """:class:`int`: The player's Light Cone count."""
    avatars: int = field(name="avatar_count")
    """:class:`int`: The player's Avatar count."""
    achivements: int = field(name="achievement_count")
    """:class:`int`: The player's unlocked Achievement count."""


class PlayerInfo(MihomoBase, frozen=True):
    id: str = field(name="uid")
    """:class:`str`: The UID of the player."""
    name: str = field(name="nickname")
    """:class:`str`: The name of the player."""
    avatar: PlayerAvatar
    """:class:`PlayerAvatar`: The avatar of the player."""
    signature: str | None
    """:class:`str | None`: The signature of the player."""
    display: bool = field(name="is_display")
    """:class:`bool`: Whether the player is displayed/public."""
    progression: PlayerProgression = field(name="space_info")
    """:class:`PlayerProgression`: The progression of the player."""
    level: int = field(default=1)
    """:class:`int`: The level of the player."""
    equilibrium_level: int = field(name="world_level", default=1)
    """:class:`int`: The equilibrium/world level of the player."""
    friend_count: int = field(default=0)
    """:class:`int`: The friend count of the player."""


class Player(MihomoBase, frozen=True):
    player: PlayerInfo
    """:class:`PlayerInfo`: The player information."""
    characters: list[Character] = field(default_factory=list)
    """:class:`list[Character]`: The characters displayed by the player."""
