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

from datetime import datetime as dt
from datetime import timedelta, timezone
from enum import Enum

from msgspec import Struct

__all__ = (
    "HYElementType",
    "ChronicleDate",
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

    @property
    def icon_url(self) -> str:
        """:class:`str`: The URL of the element's icon."""
        if self == HYElementType.Unknown:
            return "icon/element/None.png"
        return f"icon/element/{self.name}.png"


class ChronicleDate(Struct):
    year: int
    """:class:`int`: The year of the date."""
    month: int
    """:class:`int`: The month of the date."""
    day: int
    """:class:`int`: The day of the date."""
    hour: int
    """:class:`int`: The hour of the date."""
    minute: int
    """:class:`int`: The minute of the date."""

    @property
    def datetime(self) -> dt:
        tz = timezone(timedelta(hours=8), "Asia/Shanghai")
        return dt(self.year, self.month, self.day, self.hour, self.minute, tzinfo=tz)
