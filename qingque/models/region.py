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

from enum import Enum, auto
from typing import overload

__all__ = (
    "HYVServer",
    "HYVRegion",
)


class HYVServer(int, Enum):
    ChinaA = 1
    ChinaB = 2
    ChinaC = 5
    NorthAmerica = 6
    Europe = 7
    Asia = 8
    Taiwan = 9

    @overload
    @classmethod
    def from_uid(cls: type[HYVServer], uid: str) -> HYVServer:
        ...

    @overload
    @classmethod
    def from_uid(cls: type[HYVServer], uid: str, *, ignore_error: bool = True) -> HYVServer | None:
        ...

    @classmethod
    def from_uid(cls: type[HYVServer], uid: str, *, ignore_error: bool = False) -> HYVServer | None:
        try:
            return cls(int(uid[0]))
        except ValueError:
            if ignore_error:
                return None
            raise

    @property
    def short(self) -> str:
        match self:
            case HYVServer.ChinaA | HYVServer.ChinaB | HYVServer.ChinaC:
                return "China"
            case HYVServer.NorthAmerica:
                return "NA"
            case HYVServer.Europe:
                return "EU"
            case HYVServer.Asia:
                return "Asia"
            case HYVServer.Taiwan:
                return "TW/HK/MO"

    @property
    def pretty(self) -> str:
        match self:
            case HYVServer.ChinaA | HYVServer.ChinaB | HYVServer.ChinaC:
                return "Mainland China"
            case HYVServer.NorthAmerica:
                return "North America"
            case HYVServer.Europe:
                return "Europe"
            case HYVServer.Asia:
                return "Asia"
            case HYVServer.Taiwan:
                return "Taiwan/Hong Kong/Macau"


class HYVRegion(int, Enum):
    China = auto()
    Overseas = auto()

    @classmethod
    def from_server(cls: type[HYVRegion], server: HYVServer) -> HYVRegion:
        if server in (HYVServer.ChinaA, HYVServer.ChinaB, HYVServer.ChinaC):
            return cls.China
        return cls.Overseas

    @classmethod
    def from_uid(cls: type[HYVRegion], uid: str) -> HYVRegion:
        return cls.from_server(HYVServer.from_uid(uid))
