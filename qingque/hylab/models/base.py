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
from typing import Generic, TypeVar

import msgspec
from msgspec import Struct, field

from .errors import (
    ERRORS,
    HYAuthkeyException,
    HYAuthkeyTimeout,
    HYGeetestTriggered,
    HYInvalidAuthkey,
    HYLabException,
    HYRedemptionException,
)

__all__ = (
    "HYLanguage",
    "HYResponse",
    "HYGeeTestError",
    "HYGeeTestResponse",
    "RespT",
)
RespT = TypeVar("RespT", bound=Struct)


class HYGeeTestError(Struct):
    risk_code: int
    gt: str
    challenge: str
    success: int


class HYGeeTestResponse(Struct):
    gt_result: HYGeeTestError


class HYResponse(Struct, Generic[RespT], omit_defaults=True):
    code: int = field(name="retcode", default=0)
    """:class:`int`: The response code."""
    message: str = field(name="message", default="OK")
    """:class:`str`: The response message."""
    data: RespT | None = field(name="data", default=None)
    """:class:`RespT | None`: The response data."""

    def raise_for_status(self) -> None:
        if self.message.startswith("authkey"):
            if self.code == -100:
                raise HYInvalidAuthkey(self)
            elif self.code == -101:
                raise HYAuthkeyTimeout(self)
            else:
                raise HYAuthkeyException(self)

        if self.code in ERRORS:
            exctype, msg = ERRORS[self.code]
            raise exctype(self, msg)

        if "redemption" in self.message:
            raise HYRedemptionException(self)

        if self.code != 0:
            raise HYLabException(self)

    @classmethod
    def make_response(cls: type[HYResponse[RespT]], data: bytes, *, type: type[RespT]) -> "HYResponse"[RespT]:
        try:
            resp = msgspec.json.decode(data, type=HYResponse[HYGeeTestResponse])
            if resp.data is not None:
                raise HYGeetestTriggered(resp)
        except msgspec.DecodeError:
            # Not geetest error
            pass

        resp = msgspec.json.decode(data, type=HYResponse[type])
        return resp


class HYLanguage(str, Enum):
    CHS = "zh-cn"
    """Chinese Simplified"""
    CHT = "zh-tw"
    """Chinese Traditional"""
    DE = "de-de"
    """German"""
    EN = "en-us"
    """English (US)"""
    ES = "es-es"
    """Spanish"""
    FR = "fr-fr"
    """French"""
    ID = "id-id"
    """Indonesian"""
    IT = "it-it"
    """Italian"""
    JP = "ja-jp"
    """Japanese"""
    KR = "ko-kr"
    """Korean"""
    PT = "pt-pt"
    """Portuguese"""
    RU = "ru-ru"
    """Russian"""
    TH = "th-th"
    """Thai"""
    TR = "tr-tr"
    """Turkish"""
    VN = "vi-vn"
    """Vietnamese"""
