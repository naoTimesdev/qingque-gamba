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

import asyncio
from typing import Any, Mapping, TypeVar

import aiohttp
import msgspec
import yarl

from qingque.models.region import HYVRegion, HYVServer

from .constants import CHRONICLES_ROUTE, STARRAIL_SERVER, USER_AGENT
from .ds import get_ds_headers
from .models.base import HYLanguage, HYResponse
from .models.characters import ChronicleCharacters
from .models.notes import ChronicleNotes
from .models.overview import ChronicleOverview, ChronicleUserInfo, ChronicleUserOverview

__all__ = ("HYLabClient",)
HYModelT = TypeVar("HYModelT", bound=msgspec.Struct)


class HYLabClient:
    HOYOLAB = "https://act.hoyolab.com"

    def __init__(self, ltuid: int, ltoken: str) -> None:
        self._ltuid = ltuid
        self._ltoken = ltoken
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
        url: yarl.URL,
        body: Mapping[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        cookies: dict[str, str] | None = None,
        *,
        type: type[HYModelT],
        **kwargs: Any,
    ) -> HYResponse[HYModelT]:
        # Assume that the body is JSON for POST, and query for GET
        headers = headers or {}
        method = method.upper()
        headers.update(
            {
                "Accept": "application/json;charset=UTF-8",
                "Host": url.host or self.HOYOLAB,
                "Referer": f"{self.HOYOLAB}/",
                "User-Agent": USER_AGENT,
                "Origin": self.HOYOLAB,
            }
        )
        default_cookies = {
            "ltuid": str(self._ltuid),
            "ltoken": self._ltoken,
        }
        if cookies is not None:
            default_cookies.update(cookies)

        kwargs_body: dict[str, Any] = {
            "headers": headers,
            "cookies": default_cookies,
        }
        if body is not None and method == "POST":
            kwargs_body["json"] = body
        elif body is not None and method == "GET":
            kwargs_body["params"] = body
        kwargs.pop("headers", None)
        kwargs.pop("json", None)
        kwargs.pop("params", None)
        kwargs.pop("data", None)
        kwargs.pop("cookies", None)
        kwargs_body.update(kwargs)

        req = await self._client.request(method, url, **kwargs_body)
        req.raise_for_status()

        if "application/json" not in req.content_type:
            raise ValueError(f"Expected JSON response, got {req.content_type}")

        data_bytes = await req.read()
        decoded = HYResponse[type].make_response(data_bytes, type=type)
        req.close()
        decoded.raise_for_status()
        return decoded

    def _create_hylab_cookie(
        self, hylab_id: int | None, hylab_token: str | None, hylab_cookie: str | None, lang: HYLanguage = HYLanguage.EN
    ) -> dict[str, str]:
        cookies: dict[str, str] = {"mi18nLang": lang.value}
        if hylab_id is not None:
            cookies["ltuid"] = str(hylab_id)
        if hylab_token is not None:
            cookies["ltoken"] = hylab_token
        if hylab_cookie is not None:
            cookies["cookie_token"] = hylab_cookie
        return cookies

    async def get_battle_chronicles_overview(
        self,
        uid: int,
        *,
        hylab_id: int | None = None,
        hylab_token: str | None = None,
        hylab_cookie: str | None = None,
        lang: HYLanguage = HYLanguage.EN,
    ) -> ChronicleUserOverview:
        """
        Get the battle chronicles overview for the given UID.

        Parameters
        ----------
        uid: :class:`int`
            The UID to get the battle chronicles for.
        hylab_id: :class:`int | None`
            Override HoyoLab ID. (ltuid)
        hylab_token: :class:`str | None`
            Override HoyoLab token. (ltoken)
        hylab_cookie: :class:`str | None`
            Override HoyoLab cookie token. (cookie_token)
        lang: :class:`HYLanguage`
            The language to use.

        Returns
        -------
        :class:`ChronicleUserOverview`
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

        params = {
            "server": STARRAIL_SERVER[server],
            "role_id": str(uid),
        }

        index_req = self._request(
            "GET",
            CHRONICLES_ROUTE.get_route(region) / "index",
            params,
            get_ds_headers(HYVRegion.from_server(server), lang=lang),
            cookies=self._create_hylab_cookie(hylab_id, hylab_token, hylab_cookie, lang=lang),
            type=ChronicleOverview,
        )
        basic_info_req = self._request(
            "GET",
            CHRONICLES_ROUTE.get_route(region) / "role" / "basicInfo",
            params,
            get_ds_headers(HYVRegion.from_server(server), lang=lang),
            cookies=self._create_hylab_cookie(hylab_id, hylab_token, hylab_cookie, lang=lang),
            type=ChronicleUserInfo,
        )

        resp_index, resp_basic = await asyncio.gather(index_req, basic_info_req)

        return ChronicleUserOverview(resp_basic.data, resp_index.data)

    async def get_battle_chronicles_notes(
        self,
        uid: int,
        *,
        hylab_id: int | None = None,
        hylab_token: str | None = None,
        hylab_cookie: str | None = None,
        lang: HYLanguage = HYLanguage.EN,
    ) -> ChronicleNotes | None:
        """
        Get the battle chronicles real-time notes for the given UID.

        Parameters
        ----------
        uid: :class:`int`
            The UID to get the battle chronicles for.
        hylab_id: :class:`int | None`
            Override HoyoLab ID. (ltuid)
        hylab_token: :class:`str | None`
            Override HoyoLab token. (ltoken)
        hylab_cookie: :class:`str | None`
            Override HoyoLab cookie token. (cookie_token)
        lang: :class:`HYLanguage`
            The language to use.

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

        params = {
            "server": STARRAIL_SERVER[server],
            "role_id": str(uid),
        }

        resp = await self._request(
            "GET",
            CHRONICLES_ROUTE.get_route(region) / "note",
            params,
            get_ds_headers(HYVRegion.from_server(server), lang=lang),
            cookies=self._create_hylab_cookie(hylab_id, hylab_token, hylab_cookie, lang=lang),
            type=ChronicleNotes,
        )

        return resp.data

    async def get_battle_chronicles_characters(
        self,
        uid: int,
        *,
        hylab_id: int | None = None,
        hylab_token: str | None = None,
        hylab_cookie: str | None = None,
        lang: HYLanguage = HYLanguage.EN,
    ) -> ChronicleCharacters | None:
        """
        Get the battle chronicles characters for the given UID.

        Parameters
        ----------
        uid: :class:`int`
            The UID to get the battle chronicles for.
        hylab_id: :class:`int | None`
            Override HoyoLab ID. (ltuid)
        hylab_token: :class:`str | None`
            Override HoyoLab token. (ltoken)
        hylab_cookie: :class:`str | None`
            Override HoyoLab cookie token. (cookie_token)
        lang: :class:`HYLanguage`
            The language to use.

        Returns
        -------
        :class:`ChronicleCharacters`
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

        params = {
            "server": STARRAIL_SERVER[server],
            "role_id": str(uid),
        }

        resp = await self._request(
            "GET",
            CHRONICLES_ROUTE.get_route(region) / "avatar" / "info",
            params,
            get_ds_headers(HYVRegion.from_server(server), lang=lang),
            cookies=self._create_hylab_cookie(hylab_id, hylab_token, hylab_cookie, lang=lang),
            type=ChronicleCharacters,
        )

        return resp.data
