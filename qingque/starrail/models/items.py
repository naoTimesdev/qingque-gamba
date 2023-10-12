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

from .base import SRSBase

__all__ = (
    "SRSItemType",
    "SRSItem",
)


class SRSItemType(str, Enum):
    Consumable = "Usable"
    """Any consumable items."""
    Equipment = "Display"
    """Any equipment items."""
    Material = "Material"
    """Any material items."""
    Mission = "Mission"
    """Any mission exclusive items."""
    Food = "Food"
    """Any food items."""
    Formula = "Formula"
    """Any formula items, used in Synthetizer."""
    Gift = "Gift"
    """Any gift items."""
    ForcedGift = "ForceOpitonalGift"
    """Any forced gift items."""
    RelicSets = "RelicSetShowOnly"
    """Any relic sets."""
    RelicRarity = "RelicRarityShowOnly"
    """Any relic rarity items."""
    Book = "Book"
    """Any book items."""
    ChatBubble = "ChatBubble"
    """Any chat bubble items."""
    PhoneTheme = "PhoneTheme"
    """Any phone theme items."""
    Museum = "MuseumExhibit"
    """Any museum exhibit items."""
    MuseumStaff = "MuseumStuff"
    """Any museum staff items."""
    AetherSkill = "AetherSkill"
    """Any aethereum wars skill items."""
    AetherSpirit = "AetherSpirit"
    """Any aethereum wars spirit/character items."""
    Other = "Virtual"
    """Any other items."""
    Unknown1 = "GameplayCounter"


class SRSItem(SRSBase, frozen=True):
    id: str
    """:class:`str`: The item ID."""
    name: str
    """:class:`str`: The item name."""
    type: SRSItemType
    """:class:`SRSItemType`: The item type."""
    sub_type: SRSItemType
    """:class:`SRSItemType`: The item sub type."""
    rarity: int
    """:class:`int`: The item rarity."""
    icon_url: str = field(name="icon")
    """:class:`str`: The item icon URL."""
    sources: list[str] = field(default_factory=list, name="come_from")
    """:class:`list[str]`: The item whereabouts."""
