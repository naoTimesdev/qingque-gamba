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

from .player import PlayerForgottenHall

__all__ = (
    "get_uid_region",
    "get_actual_moc_floor",
)


def get_uid_region(uid: str | int) -> str | None:
    """Get the region from the UID.

    Parameters
    ----------
    uid: :class:`str | int`
        The UID.

    Returns
    -------
    :class:`str | None`
        The region.
    """

    region = str(uid)[0]
    match region:
        case "1" | "2" | "5":
            return "China"
        case "6":
            return "NA"
        case "7":
            return "EU"
        case "8":
            return "Asia"
        case "9":
            return "TW/HK/MO"
        case _:
            return None


def get_actual_moc_floor(forgotten_hall: PlayerForgottenHall) -> PlayerForgottenHall:
    """Get the actual MoC floor from the player's data.

    Some players have their MoC floor ID and finished floor ID swapped.

    Parameters
    ----------
    forgotten_hall: :class:`PlayerForgottenHall`
        The player's Forgotten Hall data.

    Returns
    -------
    :class:`PlayerForgottenHall`
        The fixed Forgotten Hall data.
    """
    if forgotten_hall.finished_floor >= 100:
        return PlayerForgottenHall(
            finished_floor=forgotten_hall.moc_finished_floor,
            moc_floor_id=forgotten_hall.finished_floor,
            moc_finished_floor=forgotten_hall.moc_floor_id,
        )
    return forgotten_hall
