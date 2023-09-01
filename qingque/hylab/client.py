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

from typing import Any, Mapping, TypeVar

import aiohttp
import msgspec
import yarl

from qingque.models.region import HYVRegion, HYVServer

from .constants import CHRONICLES_ROUTE, STARRAIL_SERVER, USER_AGENT
from .ds import get_ds_headers
from .models.base import HYResponse
from .models.notes import ChronicleNotes
from .models.overview import ChronicleOverview

__all__ = ("HYLabClient",)
HYModelT = TypeVar("HYModelT", bound=msgspec.Struct)


class HYLabClient:
    def __init__(self) -> None:
        self._client = aiohttp.ClientSession(
            headers={
                "User-Agent": USER_AGENT,
            }
        )

    async def close(self) -> None:
        await self._client.close()

    async def _request(
        self,
        method: str,
        url: str | yarl.URL,
        body: Mapping[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        *,
        type: type[HYModelT],
        **kwargs: Any,
    ) -> HYResponse[HYModelT]:
        # Assume that the body is JSON for POST, and query for GET
        headers = headers or {}
        method = method.upper()
        if method == "POST":
            headers.update({"Content-Type": "application/json;charset=UTF-8"})

        kwargs_body: dict[str, Any] = {
            "headers": headers,
        }
        if body is not None and method == "POST":
            kwargs_body["json"] = body
        elif body is not None and method == "GET":
            kwargs_body["params"] = body
        kwargs.pop("headers", None)
        kwargs.pop("json", None)
        kwargs.pop("params", None)
        kwargs.pop("data", None)
        kwargs_body.update(kwargs)

        req = await self._client.request(method, url)
        req.raise_for_status()

        if "application/json" not in req.content_type:
            raise ValueError(f"Expected JSON response, got {req.content_type}")

        decoded = HYResponse[type].make_response(await req.read())
        req.close()
        decoded.raise_for_status()
        return decoded

    def _create_hylab_cookie(self, hylab_id: int, hylab_token: str, lang: str = "en-us"):
        return f"ltuid={hylab_id}; ltoken={hylab_token}; mi18nLang={lang}"

    async def get_battle_chronicles_overview(self, uid: int, *, hylab_id: int, hylab_token: str, lang: str = "en-us"):
        """
        Get the battle chronicles overview for the given UID.

        Parameters
        ----------
        uid: :class:`int`
            The UID to get the battle chronicles for.
        hylab_id: :class:`int`
            The HoyoLab ID.
        hylab_token: :class:`str`
            The HoyoLab token.

        Returns
        -------
        :class:`ChronicleNotes`
            The battle chronicles for the given UID.

        Raises
        ------
        :exc:`.HYLabException`
            An error occurred while getting the battle chronicles.
        :exc:`aiohttp.ClientResponseError`
            An error occurred while requesting the battle chronicles.
        """

        server = HYVServer.from_uid(str(uid))
        region = HYVRegion.from_server(server)
        headers = get_ds_headers(HYVRegion.from_server(server), lang=lang)
        headers.update(
            {
                "Cookie": self._create_hylab_cookie(hylab_id, hylab_token, lang=lang),
            }
        )

        params = {
            "server": STARRAIL_SERVER[server],
            "role_id": str(uid),
        }

        resp = await self._request(
            "GET",
            CHRONICLES_ROUTE.get_route(region) / "index",
            params,
            headers,
            type=ChronicleOverview,
        )

        return resp.data

    async def get_battle_chronicles_notes(self, uid: int, *, hylab_id: int, hylab_token: str, lang: str = "en-us"):
        """
        Get the battle chronicles real-time notes for the given UID.

        Parameters
        ----------
        uid: :class:`int`
            The UID to get the battle chronicles for.
        hylab_id: :class:`int`
            The HoyoLab ID.
        hylab_token: :class:`str`
            The HoyoLab token.

        Returns
        -------
        :class:`ChronicleNotes`
            The battle chronicles for the given UID.

        Raises
        ------
        :exc:`.HYLabException`
            An error occurred while getting the battle chronicles.
        :exc:`aiohttp.ClientResponseError`
            An error occurred while requesting the battle chronicles.
        """

        server = HYVServer.from_uid(str(uid))
        region = HYVRegion.from_server(server)
        headers = get_ds_headers(HYVRegion.from_server(server), lang=lang)
        headers.update(
            {
                "Cookie": self._create_hylab_cookie(hylab_id, hylab_token, lang=lang),
            }
        )

        params = {
            "server": STARRAIL_SERVER[server],
            "role_id": str(uid),
        }

        resp = await self._request(
            "GET",
            CHRONICLES_ROUTE.get_route(region) / "note",
            params,
            headers,
            type=ChronicleNotes,
        )

        return resp.data
