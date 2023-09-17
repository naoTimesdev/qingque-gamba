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

from typing import Any

import discord
from discord.components import SelectOption
from discord.interactions import Interaction
from discord.ui.item import Item
from discord.utils import MISSING

from qingque.bot import QingqueClient
from qingque.i18n import PartialTranslate, get_i18n_discord
from qingque.models.persistence import QingqueProfileV2Game, QingqueProfileV2GameKind
from qingque.models.region import HYVServer

__all__ = ("AccountSelectView",)


def _get_player_server(server: HYVServer, t: PartialTranslate) -> str:
    match server:
        case HYVServer.ChinaA | HYVServer.ChinaB | HYVServer.ChinaC:
            return t("region.short.china")
        case HYVServer.NorthAmerica:
            return t("region.short.na")
        case HYVServer.Europe:
            return t("region.short.eur")
        case HYVServer.Asia:
            return t("region.short.asia")
        case HYVServer.Taiwan:
            return t("region.short.taiwan")


def _get_player_game_kind(kind: QingqueProfileV2GameKind, t: PartialTranslate) -> str:
    match kind:
        case QingqueProfileV2GameKind.StarRail:
            return t("game_kind.starrail")


def _get_player_server_emoji(server: HYVServer) -> str:
    match server:
        case HYVServer.ChinaA | HYVServer.ChinaB | HYVServer.ChinaC:
            return "🇨🇳"
        case HYVServer.NorthAmerica:
            return "🇺🇸"
        case HYVServer.Europe:
            return "🇪🇺"
        case HYVServer.Asia:
            return "🇸🇬"
        case HYVServer.Taiwan:
            return "🇹🇼"


class AccountSelect(discord.ui.Select):
    def __init__(
        self,
        parent: "AccountSelectView",
        accounts: list[QingqueProfileV2Game],
        locale: discord.Locale,
        *,
        custom_id: str = MISSING,
        placeholder: str | None = None,
        disabled: bool = False,
    ) -> None:
        self._parent_view = parent
        t = get_i18n_discord(locale)

        options: list[SelectOption] = []
        for game in accounts:
            value_fmt = t(
                "srchoices.value_format",
                {
                    "game": _get_player_game_kind(game.kind, t),
                    "uid": str(game.uid),
                    "region": _get_player_server(game.server, t),
                },
            )
            opts = SelectOption(
                label=value_fmt,
                value=str(game.uid),
                emoji=_get_player_server_emoji(game.server),
            )
            options.append(opts)
        self._games = accounts

        super().__init__(custom_id=custom_id, placeholder=placeholder, disabled=disabled, options=options)

    async def callback(self, interaction: Interaction[QingqueClient]) -> Any:
        try:
            first_val = self.values[0]
        except IndexError:
            return self._parent_view.set_response(None)

        for game in self._games:
            if str(game.uid) == first_val:
                return self._parent_view.set_response(game)
        self._parent_view.set_response(None)


class AccountSelectView(discord.ui.View):
    def __init__(
        self, accounts: list[QingqueProfileV2Game], locale: discord.Locale, *, timeout: float | None = 180
    ) -> None:
        super().__init__(timeout=timeout)

        self.add_item(
            AccountSelect(
                self,
                accounts=accounts,
                locale=locale,
            )
        )

        self._response: QingqueProfileV2Game | None = None
        self._error: Exception | None = None

    @property
    def account(self) -> QingqueProfileV2Game | None:
        return self._response

    @property
    def error(self) -> Exception | None:
        return self._error

    def set_response(self, account: QingqueProfileV2Game | None) -> None:
        self._response = account
        self.stop()

    async def on_timeout(self) -> None:
        self.set_response(None)
        self.stop()

    async def on_error(self, interaction: Interaction[QingqueClient], error: Exception, item: Item[Any]) -> None:
        self._error = error
        self.set_response(None)
        self.stop()
