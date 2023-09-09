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
from typing import Any, Mapping, TypeVar, overload
from uuid import uuid4

import aiohttp
import msgspec
import yarl

from qingque.hylab.interceptor import log_request
from qingque.models.region import HYVRegion, HYVServer

from .constants import CHRONICLES_ROUTE, DAILY_ROUTE, DS_SALT, STARRAIL_SERVER, USER_AGENT
from .ds import generate_dynamic_salt, get_ds_headers
from .models.base import HYLanguage, HYResponse
from .models.characters import ChronicleCharacters
from .models.forgotten_hall import ChronicleForgottenHall
from .models.notes import ChronicleNotes
from .models.overview import ChronicleOverview, ChronicleUserInfo, ChronicleUserOverview
from .models.simuniverse import ChronicleSimulatedUniverse, ChronicleSimulatedUniverseSwarmDLC

__all__ = ("HYLabClient",)
HYModelT = TypeVar("HYModelT", bound=msgspec.Struct)


class HYLabClient:
    HOYOLAB = "https://act.hoyolab.com"

    def __init__(self, ltuid: int, ltoken: str) -> None:
        self._ltuid = ltuid
        self._ltoken = ltoken
        trace_conf = aiohttp.TraceConfig()
        trace_conf.on_request_start.append(log_request)
        self._client = aiohttp.ClientSession(
            trace_configs=[trace_conf],
            headers={
                "User-Agent": USER_AGENT,
            },
        )

    async def close(self) -> None:
        await self._client.close()

    @overload
    async def _request(
        self,
        method: str,
        url: yarl.URL,
        body: Mapping[str, Any] | None = ...,
        headers: dict[str, Any] | None = ...,
        cookies: dict[str, str] | None = ...,
        params: Mapping[str, Any] | None = ...,
        *,
        type: type[HYModelT],
        **kwargs: Any,
    ) -> HYResponse[HYModelT]:
        ...

    @overload
    async def _request(
        self,
        method: str,
        url: yarl.URL,
        body: Mapping[str, Any] | None = ...,
        headers: dict[str, Any] | None = ...,
        cookies: dict[str, str] | None = ...,
        params: Mapping[str, Any] | None = ...,
        *,
        type: None,
        **kwargs: Any,
    ) -> None:
        ...

    async def _request(
        self,
        method: str,
        url: yarl.URL,
        body: Mapping[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        cookies: dict[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
        *,
        type: type[HYModelT] | None = None,
        **kwargs: Any,
    ) -> HYResponse[HYModelT] | None:
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
        if params is not None:
            kwargs_body["params"] = params
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

        # Check if success code is HTTP Status COde Empty
        if req.status in (204, 205):
            return HYResponse.default()

        data_bytes = await req.read()
        if type is None:
            return None
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
            The battle chronicles overview for the given UID.

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
            The battle chronicles real-time notes for the given UID.

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
            The battle chronicles characters for the given UID.

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

    async def get_battle_chronicles_forgotten_hall(
        self,
        uid: int,
        *,
        previous: bool = False,
        hylab_id: int | None = None,
        hylab_token: str | None = None,
        hylab_cookie: str | None = None,
        lang: HYLanguage = HYLanguage.EN,
    ) -> ChronicleForgottenHall | None:
        """
        Get the battle chronicles forgotten hall for the given UID.

        Parameters
        ----------
        uid: :class:`int`
            The UID to get the battle chronicles for.
        previous: :class:`bool`
            Whether to get the previous record or not.
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
        :class:`ChronicleForgottenHall`
            The battle chronicles forgotten hall for the given UID.

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
            "schedule_type": 2 if previous else 1,
            "need_all": "true",
        }

        resp = await self._request(
            "GET",
            CHRONICLES_ROUTE.get_route(region) / "challenge",
            params,
            get_ds_headers(HYVRegion.from_server(server), lang=lang),
            cookies=self._create_hylab_cookie(hylab_id, hylab_token, hylab_cookie, lang=lang),
            type=ChronicleForgottenHall,
        )

        return resp.data

    async def get_battle_chronicles_simulated_universe(
        self,
        uid: int,
        *,
        hylab_id: int | None = None,
        hylab_token: str | None = None,
        hylab_cookie: str | None = None,
        lang: HYLanguage = HYLanguage.EN,
    ) -> ChronicleSimulatedUniverse | None:
        """
        Get the battle chronicles simulated universe for the given UID.

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
        :class:`ChronicleSimulatedUniverse`
            The battle chronicles simulated universe for the given UID.

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
            "schedule_type": 3,
            "need_detail": "true",
        }

        resp = await self._request(
            "GET",
            CHRONICLES_ROUTE.get_route(region) / "rogue",
            params,
            get_ds_headers(HYVRegion.from_server(server), lang=lang),
            cookies=self._create_hylab_cookie(hylab_id, hylab_token, hylab_cookie, lang=lang),
            type=ChronicleSimulatedUniverse,
        )

        return resp.data

    async def get_battle_chronicles_simulated_universe_swarm_dlc(
        self,
        uid: int,
        *,
        hylab_id: int | None = None,
        hylab_token: str | None = None,
        hylab_cookie: str | None = None,
        lang: HYLanguage = HYLanguage.EN,
    ) -> ChronicleSimulatedUniverseSwarmDLC | None:
        """
        Get the battle chronicles simulated universe swarm DLC for the given UID.

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
        :class:`ChronicleSimulatedUniverseSwarmDLC`
            The battle chronicles simulated universe swarm DLC for the given UID.

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
            "need_detail": "true",
        }

        resp = await self._request(
            "GET",
            CHRONICLES_ROUTE.get_route(region) / "rogue_locust",
            params,
            get_ds_headers(HYVRegion.from_server(server), lang=lang),
            cookies=self._create_hylab_cookie(hylab_id, hylab_token, hylab_cookie, lang=lang),
            type=ChronicleSimulatedUniverseSwarmDLC,
        )

        return resp.data

    async def claim_daily_reward(
        self,
        uid: int,
        hylab_id: int,
        *,
        hylab_token: str | None = None,
        hylab_cookie: str | None = None,
        lang: HYLanguage = HYLanguage.EN,
    ) -> None:
        """
        Claim HoyoLab daily reward for the given UID/HoyoLab ID.

        Parameters
        ----------
        uid: :class:`int`
            The UID to get the battle chronicles for.
        hylab_id: :class:`int`
            HoyoLab ID. (ltuid)
        hylab_token: :class:`str | None`
            Override HoyoLab token. (ltoken)
        hylab_cookie: :class:`str | None`
            Override HoyoLab cookie token. (cookie_token)
        lang: :class:`HYLanguage`
            The language to use.

        Returns
        -------
        :class:`None`
            Successfully claimed the daily reward.

        Raises
        ------
        :exc:`.HYLabException`
            An error occurred while claiming the daily reward.
        :exc:`aiohttp.ClientResponseError`
            An error occurred while requesting the daily reward claim.
        """

        server = HYVServer.from_uid(str(uid))
        region = HYVRegion.from_server(server)

        headers = {}
        params = {}
        if region == HYVRegion.Overseas:
            params["lang"] = lang.value
            headers["referer"] = "https://act.hoyolab.com/"
        elif region == HYVRegion.China:
            params["uid"] = str(uid)
            params["region"] = STARRAIL_SERVER[server]

            headers["x-rpc-app_version"] = "2.34.1"
            headers["x-rpc-client_type"] = "5"
            headers["x-rpc-device_id"] = str(uuid4())
            headers["x-rpc-sys_version"] = "12"
            headers["x-rpc-platform"] = "android"
            headers["x-rpc-channel"] = "miyousheluodi"
            headers["x-rpc-device_model"] = hylab_id or ""
            headers["referer"] = (
                "https://webstatic.mihoyo.com/bbs/event/signin-ys/index.html?"
                "bbs_auth_required=true&act_id=e202009291139501&utm_source=bbs&utm_medium=mys&utm_campaign=icon"
            )

            headers["ds"] = generate_dynamic_salt(DS_SALT["cn_signin"])
        else:
            raise ValueError(f"Unknown region {region}")

        route = DAILY_ROUTE.get_route(region)
        sign_route = (route / "sign").update_query(**route.query)

        cookies = self._create_hylab_cookie(hylab_id, hylab_token, hylab_cookie, lang=lang)

        await self._request("POST", sign_route, params=params, headers=headers, cookies=cookies, type=None)
