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

from typing import TypeVar

import aiohttp
import msgspec

from qingque.mihomo.models import BASE_URL, MihomoLanguage, Player

__all__ = ("MihomoAPI",)
MihomoT = TypeVar("MihomoT", bound=msgspec.Struct)


class MihomoAPI:
    def __init__(self, *, client: aiohttp.ClientSession | None = None) -> None:
        self.client = client or aiohttp.ClientSession(
            headers={
                "User-Agent": "Qingque-Client/0.1.0",
            },
        )
        self._outside_client: bool = client is not None

    async def close(self):
        """Close the underlying HTTP session.

        Only works if the client is created by the library.
        """

        if not self._outside_client:
            await self.client.close()

    async def _make_response(self, response: aiohttp.ClientResponse, *, type: type[MihomoT]) -> MihomoT:
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
        return msgspec.json.decode(await response.read(), type=type)

    async def get_player(
        self, uid: int, *, language: MihomoLanguage = MihomoLanguage.EN
    ) -> tuple[Player, MihomoLanguage]:
        """Get a player by their UID.

        Parameters
        ----------
        uid: :class:`int`
            The UID of the player.
        language: :class:`MihomoLanguage`, optional
            The language to use for the response. Defaults to :attr:`MihomoLanguage.EN`.

        Returns
        -------
        tuple[:class:`Player`, :class:`MihomoLanguage`]
            The player object and the language used for the response.

        Raises
        ------
        :exc:`aiohttp.ClientResponseError`
            If the API returns an error.
        """

        resp = await self.client.get(f"{BASE_URL}/{uid}", params={"lang": language.value})
        data = await self._make_response(resp, type=Player)
        return data, language
