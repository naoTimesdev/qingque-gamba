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

# A tiny-wrapper for Qingque API

from __future__ import annotations

from typing import Generic, TypeVar

import aiohttp
import msgspec

from qingque.i18n import QingqueLanguage
from qingque.mihomo.models.player import Player

__all__ = (
    "ExchangeResult",
    "QingqueAPI",
    "WrappedResponse",
)
DataT = TypeVar("DataT", bound=msgspec.Struct)


class ExchangeResult(msgspec.Struct):
    token: str
    validity: int


class WrappedResponse(msgspec.Struct, Generic[DataT]):
    code: int
    message: str
    data: DataT | None


class QingqueAPI:
    def __init__(
        self, base_url: str, token_exchange: str | None = None, *, client: aiohttp.ClientSession | None = None
    ) -> None:
        default_headers = {
            "User-Agent": "Qingque-Bot/0.1.0 (+https://github.com/naoTimesdev/qingque-gamba)",
        }
        if token_exchange:
            default_headers["X-Strict-Token"] = token_exchange

        self._base_url = base_url
        self._client = client or aiohttp.ClientSession(
            base_url=base_url,
            headers=default_headers,
        )
        self._outside_client = client is not None

    async def close(self) -> None:
        if not self._outside_client:
            await self._client.close()

    async def _make_response(self, response: aiohttp.ClientResponse, *, type: type[DataT]) -> WrappedResponse[DataT]:
        """Create an entity response from the given HTTP response.

        Parameters
        ----------
        response: :class:`aiohttp.ClientResponse`
            The HTTP response to create the response from.
        type: :class:`type[MihomoT]`
            The type of response to create.

        Returns
        -------
        MihomoT
            The created response.

        Raises
        ------
        :exc:`aiohttp.ClientResponseError`
            If the API returns an error.
        """

        response.raise_for_status()
        return msgspec.json.decode(await response.read(), type=WrappedResponse[type])

    async def exchange_mihomo(self, uid: int) -> ExchangeResult | None:
        resp = await self._client.post(
            "/api/exchange/mihomo",
            json={
                "uid": uid,
            },
        )
        data = await self._make_response(resp, type=ExchangeResult)
        if data.code != 0:
            raise Exception(f"Failed to exchange mihomo: {data.message}")
        return data.data

    async def exchange_hoyolab(
        self,
        *,
        uid: int,
        ltuid: int,
        ltoken: str,
        lcookie: str | None = None,
        lmid: str | None = None,
    ):
        resp = await self._client.post(
            "/api/exchange/hoyolab",
            json={
                "uid": uid,
                "ltuid": ltuid,
                "ltoken": ltoken,
                "lcookie": lcookie,
                "lmid": lmid,
            },
        )
        data = await self._make_response(resp, type=ExchangeResult)
        if data.code != 0:
            raise Exception(f"Failed to exchange mihomo: {data.message}")
        return data.data

    async def get_mihomo(self, token: str) -> Player:
        resp = await self._client.get(f"/api/mihomo?token={token}")
        try:
            data = msgspec.json.decode(await resp.read(), type=Player)
        except msgspec.DecodeError as err:
            error_decode = msgspec.json.decode(await resp.read(), type=WrappedResponse)

            raise Exception(f"Failed to get mihomo: {error_decode.message}") from err
        return data

    def get_mihomo_profile(self, character: int, token: str, lang: QingqueLanguage, *, detailed: bool = False):
        url = f"{self._base_url}/api/mihomo/profile?token={token}&lang={lang.value}&character={character}"
        if detailed:
            url += "&detailed=true"
        return url

    def get_mihomo_player(self, token: str, lang: QingqueLanguage):
        return f"{self._base_url}/api/mihomo/player?token={token}&lang={lang.value}"
