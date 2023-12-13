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

from typing import ClassVar

from discord import PartialEmoji

__all__ = ("CustomEmoji",)


class CustomEmoji:
    _LOADER_DEFAULT: ClassVar[dict[str, str]] = {
        "su_world1": "1️⃣",
        "su_world2": "2️⃣",
        "su_world3": "3️⃣",
        "su_world4": "4️⃣",
        "su_world5": "5️⃣",
        "su_world6": "6️⃣",
        "su_world7": "7️⃣",
        "su_world8": "8️⃣",
        "su_swarmdlc": "🕸️",
    }

    _LOADER_CUSTOM: ClassVar[dict[str, PartialEmoji]] = {
        "su_world1": PartialEmoji(name="_qq_su_world1", id=1149271760806613032),
        "su_world2": PartialEmoji(name="_qq_su_world2", id=1149271767332946011),
        "su_world3": PartialEmoji(name="_qq_su_world3", id=1149271772445823026),
        "su_world4": PartialEmoji(name="_qq_su_world4", id=1149271778317828166),
        "su_world5": PartialEmoji(name="_qq_su_world5", id=1149271784705769553),
        "su_world6": PartialEmoji(name="_qq_su_world6", id=1149271791072727120),
        "su_world7": PartialEmoji(name="_qq_su_world7", id=1149271798861541376),
        "su_world8": PartialEmoji(name="_qq_su_world8", id=1184392472403648583),
        "su_swarmdlc": PartialEmoji(name="_qq_su_dlcworld", id=1149271756306141245),
    }

    def __init__(self, has_guilds: bool = False) -> None:
        self._has_guilds = has_guilds

    @property
    def has_guilds(self) -> bool:
        return self._has_guilds

    @has_guilds.setter
    def has_guilds(self, value: bool) -> None:
        self._has_guilds = bool(value)

    def get(self, key: str, /) -> str | PartialEmoji | None:
        """
        Get the emoji from the key.

        Parameters
        ----------
        key: :class:`str`
            The key to get the emoji.

        Returns
        -------
        :class:`str` | :class:`discord.PartialEmoji` | :class:`None`
            The emoji from the key.
        """

        if self._has_guilds:
            return self._LOADER_CUSTOM.get(key)
        return self._LOADER_DEFAULT.get(key)
