"""
MIT License

Copyright (c) 2021-present sadru (genshin.py)
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

from typing import TYPE_CHECKING, Any, Optional, TypeAlias

if TYPE_CHECKING:
    from .base import HYResponse

__all__ = (
    "ERRORS",
    "HYLabException",
    "HYInternalDatabaseError",
    "HYAccountNotFound",
    "HYDataNotPublic",
    "HYCookieException",
    "HYInvalidCookies",
    "HYTooManyRequests",
    "HYVisitsTooFrequently",
    "HYAlreadyClaimed",
    "HYGeetestTriggered",
    "HYAuthkeyException",
    "HYInvalidAuthkey",
    "HYAuthkeyTimeout",
    "HYRedemptionException",
    "HYRedemptionInvalid",
    "HYRedemptionCooldown",
    "HYRedemptionClaimed",
    "HYAccountLoginFail",
    "HYAccountHasLocked",
    "HYAccountUnsupported",
)


class HYLabException(Exception):
    """A base HoyoLab exception."""

    retcode: int = 0
    original: str = ""
    msg: str = ""

    def __init__(self, response: "HYResponse[Any]", msg: Optional[str] = None) -> None:
        self._resp = response
        self.retcode = response.code
        self.original = response.message
        self.msg = msg or self.msg or self.original

        if self.retcode:
            msg = f"[{self.retcode}] {self.msg}"
        else:
            msg = self.msg

        super().__init__(msg)

    def __repr__(self) -> str:
        response = {"retcode": self.retcode, "original": self.original}
        args = [repr(response)]
        if self.msg != self.original:
            args.append(repr(self.msg))

        return f"{type(self).__name__}({', '.join(args)})"

    @property
    def response(self) -> "HYResponse[Any]":
        """:class:`HYResponse[Any]`: The response that triggered this exception."""
        return self._resp


class HYInternalDatabaseError(HYLabException):
    """Internal database error."""

    retcode = -1


class HYAccountNotFound(HYLabException):
    """Tried to get data with an invalid uid."""

    msg = "Could not find user; uid may be invalid."


class HYDataNotPublic(HYLabException):
    """User hasn't set their data to public."""

    msg = "User's data is not public."


class HYCookieException(HYLabException):
    """Base error for cookies."""


class HYInvalidCookies(HYCookieException):
    """Cookies weren't valid."""

    retcode = -100
    msg = "Cookies are not valid."


class HYTooManyRequests(HYCookieException):
    """Made too many requests and got ratelimited."""

    retcode = 10101
    msg = "Cannot get data for more than 30 accounts per cookie per day."


class HYVisitsTooFrequently(HYLabException):
    """Visited a page too frequently.

    Must be handled with exponential backoff.
    """

    retcode = -110
    msg = "Visits too frequently."


class HYAlreadyClaimed(HYLabException):
    """Already claimed the daily reward today."""

    retcode = -5003
    msg = "Already claimed the daily reward today."


class HYGeetestTriggered(HYLabException):
    """Geetest triggered."""

    msg = "Geetest triggered during daily reward claim."


class HYAuthkeyException(HYLabException):
    """Base error for authkeys."""


class HYInvalidAuthkey(HYAuthkeyException):
    """Authkey is not valid."""

    retcode = -100
    msg = "Authkey is not valid."


class HYAuthkeyTimeout(HYAuthkeyException):
    """Authkey has timed out."""

    retcode = -101
    msg = "Authkey has timed out."


class HYRedemptionException(HYLabException):
    """Exception caused by redeeming a code."""


class HYRedemptionInvalid(HYRedemptionException):
    """Invalid redemption code."""

    msg = "Invalid redemption code."


class HYRedemptionCooldown(HYRedemptionException):
    """Redemption is on cooldown."""

    msg = "Redemption is on cooldown."


class HYRedemptionClaimed(HYRedemptionException):
    """Redemption code has been claimed already."""

    msg = "Redemption code has been claimed already."


class HYAccountLoginFail(HYLabException):
    """Account if not exists in hoyoverse (Or password incorrect)."""

    msg = "Account login failed."


class HYAccountHasLocked(HYLabException):
    """Account has logged incorrect over than 3 - 5 time(s). It's will be locked and wait 20 minute."""

    msg = "Account has been locked because exceeded password limit. Please wait 20 minute and try again"


class HYAccountUnsupported(Exception):
    """Account is not supported."""

    def __init__(self, uid: int, message: str) -> None:
        self.uid = uid
        super().__init__(f"{uid}: {message}")


_FAIL: TypeAlias = type[HYLabException]

_errors: dict[int, _FAIL | str | tuple[_FAIL, str]] = {
    # misc hoyolab
    -100: HYInvalidCookies,
    -108: "Invalid language.",
    -110: HYVisitsTooFrequently,
    # game record
    10001: HYInvalidCookies,
    -10001: "Malformed request.",
    -10002: "No game account associated with cookies.",
    # database game record
    10101: HYTooManyRequests,
    10102: HYDataNotPublic,
    10103: (HYInvalidCookies, "Cookies are valid but do not have a hoyolab account bound to them."),
    10104: "Cannot view real-time notes of other users.",
    # calculator
    -500001: "Invalid fields in calculation.",
    -500004: HYVisitsTooFrequently,
    -502001: "User does not have this character.",
    -502002: "Calculator sync is not enabled.",
    # mixin
    -1: HYInternalDatabaseError,
    1009: HYAccountNotFound,
    # redemption
    -1065: HYRedemptionInvalid,
    -1071: HYInvalidCookies,
    -1073: (HYAccountNotFound, "Account has no game account bound to it."),
    -2001: (HYRedemptionInvalid, "Redemption code has expired."),
    -2003: (HYRedemptionInvalid, "Redemption code is incorrectly formatted."),
    -2004: HYRedemptionInvalid,
    -2014: (HYRedemptionInvalid, "Redemption code not activated"),
    -2016: HYRedemptionCooldown,
    -2018: HYRedemptionClaimed,
    -2017: HYRedemptionClaimed,
    -2021: (HYRedemptionException, "Cannot claim codes for accounts with adventure rank lower than 10."),
    # rewards
    -5003: HYAlreadyClaimed,
    # chinese
    1008: HYAccountNotFound,
    -1104: "This action must be done in the app.",
    # account
    -3208: HYAccountLoginFail,
    -3202: HYAccountHasLocked,
}

ERRORS: dict[int, tuple[_FAIL, str | None]] = {
    retcode: ((exc, None) if isinstance(exc, type) else (HYLabException, exc) if isinstance(exc, str) else exc)
    for retcode, exc in _errors.items()
}
