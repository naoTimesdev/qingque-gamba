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
    "SimulatedUniverse",
    "PlayerAvatar",
    "PlayerForgottenHall",
    "PlayerProgression",
    "PlayerInfo",
    "Player",
)


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
    YanqingWorld = 8
    """World 8: Yanqing (Xianzhou) as Boss Enemy"""


class PlayerAvatar(MihomoBase, frozen=True):
    id: str
    """:class:`str`: The ID of the avatar."""
    name: str
    """:class:`str`: The name of the avatar."""
    icon_url: str = field(name="icon")
    """:class:`str`: The icon path of the avatar."""


class PlayerForgottenHall(MihomoBase, frozen=True):
    finished_floor: int = field(name="chaos_level")
    """:class:`ForgottenHallFloor`: The finished floor index of the Forgotten Hall."""
    moc_finished_floor: int = field(name="level")
    """:class:`MemoryOfChaosFloor`: The finished floor index of the Memory of Chaos."""
    moc_floor_id: int = field(name="chaos_id")
    """:class:`int`: The floor ID of the Memory of Chaos."""


class PlayerProgression(MihomoBase, frozen=True):
    forgotten_hall: PlayerForgottenHall = field(name="memory_data")
    """:class:`PlayerForgottenHall`: The player's Forgotten Hall progression."""
    simulated_universe: SimulatedUniverse = field(name="universe_level")
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
