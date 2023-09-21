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
from copy import deepcopy
from typing import Any, Mapping, TypeVar, overload
from uuid import uuid4

import aiohttp
import msgspec
import orjson
import yarl

from qingque.hylab.interceptor import log_request
from qingque.hylab.models.errors import HYAlreadyClaimed, HYGeetestTriggered
from qingque.models.region import HYVRegion, HYVServer
from qingque.tooling import get_logger

from .constants import CHRONICLES_ROUTE, DAILY_ROUTE, DS_SALT, STARRAIL_SERVER, USER_AGENT
from .ds import generate_dynamic_salt, get_ds_headers
from .models.base import HYGeeTestError, HYLanguage, HYResponse
from .models.characters import ChronicleCharacters
from .models.forgotten_hall import ChronicleForgottenHall
from .models.notes import ChronicleNotes
from .models.overview import ChronicleOverview, ChronicleUserInfo, ChronicleUserOverview
from .models.simuniverse import ChronicleSimulatedUniverse, ChronicleSimulatedUniverseSwarmDLC

__all__ = ("HYLabClient",)
HYModelT = TypeVar("HYModelT", bound=msgspec.Struct)
logger = get_logger("qingque.hylab.client")
_COOKIES_REDACT = [
    "ltuid",
    "ltuid_v2",
    "ltoken",
    "ltoken_v2",
    "cookie_token",
    "cookie_token_v2",
]


def log_with_redact(kwargs_body: dict[str, Any]):
    kwargs_body = deepcopy(kwargs_body)
    cookies = kwargs_body.get("cookies", {})
    cookie_strs = []
    for cookie_name, cookie_value in cookies.items():
        if cookie_name in _COOKIES_REDACT:
            cookie_value = cookie_value[:2] + "*" * (len(cookie_value) - 2) + cookie_value[-2:]
        cookie_strs.append(f"{cookie_name}={cookie_value}")
    kwargs_body["cookies"] = cookie_strs
    logger.debug("Requesting with %s", orjson.dumps(kwargs_body, option=orjson.OPT_INDENT_2).decode("utf-8"))


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

    def _merge_cookies(self, child: dict[str, str] | None = None) -> dict[str, str]:
        ltuid = "ltuid"
        base = {
            "ltuid": str(self._ltuid),
        }
        if self._ltoken.startswith("v2_"):
            ltuid = "ltuid_v2"
            base[ltuid] = str(self._ltuid)
            base["ltoken_v2"] = self._ltoken
        else:
            base["ltoken"] = self._ltoken
        if child is None:
            return base
        ltuid_child = child.get("ltuid", child.get("ltuid_v2", None))
        ltoken_child = child.get("ltoken", child.get("ltoken_v2", None))
        use_v2 = False
        if ltuid_child is not None and ltuid_child != str(self._ltuid) and ltoken_child is None:
            # Use parent ltuid, and ltoken.
            base[ltuid] = str(self._ltuid)
        elif ltuid_child is not None and ltuid_child != str(self._ltuid) and ltoken_child is not None:
            if ltoken_child.startswith("v2_"):
                base["ltoken_v2"] = ltoken_child
                base["ltuid_v2"] = ltuid_child
                base.pop("ltoken", None)
                base.pop("ltuid", None)
                use_v2 = True
            else:
                base["ltoken"] = ltoken_child
                base["ltuid"] = ltuid_child
        if ltmid_child := child.get("ltmid", child.get("ltmid_v2")):
            if use_v2:
                base["ltmid_v2"] = ltmid_child
            else:
                base["ltmid"] = ltmid_child
        base["mi18nLang"] = child.get("mi18nLang", HYLanguage.EN.value)
        return base

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

        kwargs_body: dict[str, Any] = {
            "headers": headers,
            "cookies": self._merge_cookies(cookies),
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

        log_with_redact(kwargs_body)

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
        self,
        hylab_id: int | None,
        hylab_token: str | None,
        hylab_cookie: str | None,
        hylab_mid_token: str | None = None,
        lang: HYLanguage = HYLanguage.EN,
    ) -> dict[str, str]:
        cookies: dict[str, str] = {"mi18nLang": lang.value}
        use_v2 = False
        if hylab_id is not None:
            cookies["ltuid"] = str(hylab_id)
        if hylab_token is not None:
            if hylab_token.startswith("v2_"):
                # Assume v2 token
                cookies["ltoken_v2"] = hylab_token
                ltuid_v1 = cookies.pop("ltuid", None)
                if ltuid_v1 is not None:
                    cookies["ltuid_v2"] = ltuid_v1
                use_v2 = True
            else:
                cookies["ltoken"] = hylab_token
        if hylab_mid_token is not None:
            cookies["ltmid_v2" if use_v2 else "ltmid"] = hylab_mid_token
        if hylab_cookie is not None:
            # TODO: Handle v2 token soon:tm:
            cookies["cookie_token"] = hylab_cookie
        return cookies

    # --> Battle Chronicles

    async def get_battle_chronicles_basic_info(
        self,
        uid: int,
        *,
        hylab_id: int | None = None,
        hylab_token: str | None = None,
        hylab_cookie: str | None = None,
        hylab_mid_token: str | None = None,
        lang: HYLanguage = HYLanguage.EN,
    ) -> ChronicleUserInfo | None:
        """
        Get the battle chronicles user basic info for the given UID.

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
        :class:`ChronicleUserInfo`
            The battle chronicles user basic info for the given UID.

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

        basic_info = await self._request(
            "GET",
            CHRONICLES_ROUTE.get_route(region) / "role" / "basicInfo",
            params,
            get_ds_headers(HYVRegion.from_server(server), lang=lang),
            cookies=self._create_hylab_cookie(hylab_id, hylab_token, hylab_cookie, hylab_mid_token, lang=lang),
            type=ChronicleUserInfo,
        )

        return basic_info.data

    async def get_battle_chronicles_overview(
        self,
        uid: int,
        *,
        hylab_id: int | None = None,
        hylab_token: str | None = None,
        hylab_cookie: str | None = None,
        hylab_mid_token: str | None = None,
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
            cookies=self._create_hylab_cookie(hylab_id, hylab_token, hylab_cookie, hylab_mid_token, lang=lang),
            type=ChronicleOverview,
        )
        basic_info_req = self.get_battle_chronicles_basic_info(
            uid, hylab_id=hylab_id, hylab_token=hylab_token, lang=lang
        )

        resp_index, resp_basic = await asyncio.gather(index_req, basic_info_req)

        return ChronicleUserOverview(resp_basic, resp_index.data)

    async def get_battle_chronicles_notes(
        self,
        uid: int,
        *,
        hylab_id: int | None = None,
        hylab_token: str | None = None,
        hylab_cookie: str | None = None,
        hylab_mid_token: str | None = None,
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
            cookies=self._create_hylab_cookie(hylab_id, hylab_token, hylab_cookie, hylab_mid_token, lang=lang),
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
        hylab_mid_token: str | None = None,
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
            cookies=self._create_hylab_cookie(hylab_id, hylab_token, hylab_cookie, hylab_mid_token, lang=lang),
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
        hylab_mid_token: str | None = None,
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
            cookies=self._create_hylab_cookie(hylab_id, hylab_token, hylab_cookie, hylab_mid_token, lang=lang),
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
        hylab_mid_token: str | None = None,
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
            cookies=self._create_hylab_cookie(hylab_id, hylab_token, hylab_cookie, hylab_mid_token, lang=lang),
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
        hylab_mid_token: str | None = None,
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
            cookies=self._create_hylab_cookie(hylab_id, hylab_token, hylab_cookie, hylab_mid_token, lang=lang),
            type=ChronicleSimulatedUniverseSwarmDLC,
        )

        return resp.data

    # <-- Battle Chronicles

    # --> Rewards

    async def claim_daily_reward(
        self,
        uid: int,
        hylab_id: int,
        *,
        hylab_token: str | None = None,
        hylab_cookie: str | None = None,
        hylab_mid_token: str | None = None,
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
        json_body = {}
        if region == HYVRegion.Overseas:
            json_body["lang"] = lang.value
            json_body["act_id"] = "e202303301540311"
            headers["referer"] = "https://act.hoyolab.com/"
        elif region == HYVRegion.China:
            json_body["uid"] = str(uid)
            json_body["region"] = STARRAIL_SERVER[server]
            json_body["act_id"] = "e202304121516551"

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

        cookies = self._create_hylab_cookie(hylab_id, hylab_token, hylab_cookie, hylab_mid_token, lang=lang)

        resp = await self._request(
            "POST",
            DAILY_ROUTE.get_route(region),
            body=json_body,
            headers=headers,
            cookies=cookies,
            type=HYGeeTestError,
        )
        if resp.data is None:
            raise ValueError("Expected JSON response, got None")

        if resp.data.success != 0:
            if resp.data.gt != "":
                raise HYGeetestTriggered(resp, None)
            raise HYAlreadyClaimed(resp, None)

    # <-- Rewards
