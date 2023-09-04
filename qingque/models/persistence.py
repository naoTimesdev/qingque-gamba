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
from functools import cached_property

from msgspec import Struct

from qingque.models.region import HYVRegion, HYVServer

__all__ = ("QingqueProfile",)


class QingqueProfile(Struct):
    id: str
    """:class:`str`: Discord ID."""
    uid: int
    """:class:`int`: The user game UID."""

    hylab_id: int | None = None
    """:class:`int | None`: The user HoyoLab ID."""
    hylab_token: str | None = None
    """:class:`str | None`: The user HoyoLab token."""


class QingqueProfileV2GameKind(str, Enum):
    StarRail = "HSR"


class QingqueProfileV2Game(Struct):
    kind: QingqueProfileV2GameKind
    """:class:`QingqueProfileV2GameKind`: The game kind."""
    uid: int
    """:class:`int`: The user game UID."""

    @cached_property
    def server(self) -> HYVServer:
        return HYVServer.from_uid(str(self.uid))

    @cached_property
    def region(self) -> HYVRegion:
        return HYVRegion.from_server(self.server)


class QingqueProfileV2(Struct):
    id: str
    """:class:`str`: Discord ID."""
    games: list[QingqueProfileV2Game]
    """:class:`list[QingqueProfileV2Game]`: The user games."""

    hylab_id: int | None = None
    """:class:`int | None`: The user HoyoLab ID."""
    hylab_token: str | None = None
    """:class:`str | None`: The user HoyoLab token."""
    hylab_cookie: str | None = None
    """:class:`str | None`: The user HoyoLab cookie."""

    @classmethod
    def from_legacy(cls: type[QingqueProfileV2], profile: QingqueProfile) -> QingqueProfileV2:
        return cls(
            id=profile.id,
            games=[
                QingqueProfileV2Game(
                    kind=QingqueProfileV2GameKind.StarRail,
                    uid=profile.uid,
                )
            ],
            hylab_id=profile.hylab_id,
            hylab_token=profile.hylab_token,
        )
