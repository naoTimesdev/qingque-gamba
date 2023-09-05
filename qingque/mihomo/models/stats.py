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

from msgspec import field as msgspec_field

from .base import MihomoBase

__all__ = (
    "StatsField",
    "StatsAtrributes",
    "StatsProperties",
    "StatsPropertiesAffix",
)


class StatsField(str, Enum):
    # Base Stats
    HP = "hp"
    ATK = "atk"
    DEF = "def"
    Speed = "spd"
    # Advanced Stats
    CritRate = "crit_rate"
    CritDamage = "crit_dmg"
    BreakEffect = "break_dmg"
    HealingRate = "heal_rate"
    EnergyRegenRate = "sp_rate"
    EffectHitRate = "effect_hit"
    EffectResist = "effect_res"
    # DMG Stats
    PhysicalBoost = "physical_dmg"
    FireBoost = "fire_dmg"
    IceBoost = "ice_dmg"
    LightningBoost = "lightning_dmg"
    WindBoost = "wind_dmg"
    QuantumBoost = "quantum_dmg"
    ImaginaryBoost = "imaginary_dmg"
    DamageBoost = "all_dmg"
    # RES Stats
    PhysicalResist = "physical_res"
    FireResist = "fire_res"
    IceResist = "ice_res"
    LightningResist = "lightning_res"
    WindResist = "wind_res"
    QuantumResist = "quantum_res"
    ImaginaryResist = "imaginary_res"
    Unknown = ""


class StatsAtrributes(MihomoBase, frozen=True):
    field: StatsField
    """:class:`StatsField`: The type of the stats."""
    name: str
    """:class:`str`: The name of the stats."""
    icon_url: str = msgspec_field(name="icon")
    """:class:`str`: The icon URL of the stats.""" ""
    value: int | float = msgspec_field(default=0)
    """:class:`int` | :class:`float`: The value of the stats."""
    display_value: str = msgspec_field(name="display", default="0")
    """:class:`str`: The display value of the stats."""
    percent: bool = msgspec_field(default=False)
    """:class:`bool`: Whether the stats is in percent or not."""


class StatsProperties(MihomoBase, frozen=True):
    type: str
    """:class:`str`: The type of the stats."""
    field: StatsField
    """:class:`StatsField`: The field type of the stats."""
    name: str
    """:class:`str`: The name of the stats."""
    icon_url: str = msgspec_field(name="icon")
    """:class:`str`: The icon URL of the stats."""
    value: int | float = msgspec_field(default=0)
    """:class:`int` | :class:`float`: The value of the stats."""
    display_value: str = msgspec_field(name="display", default="0")
    """:class:`str`: The display value of the stats."""
    percent: bool = msgspec_field(default=False)
    """:class:`bool`: Whether the stats is in percent or not."""


class StatsPropertiesAffix(StatsProperties, frozen=True):
    count: int = msgspec_field(default=0)
    """:class:`int`: How many times have this substats have been upgraded."""
    step: int = msgspec_field(default=0)
    """:class:`int`: The additional value of the substats."""
