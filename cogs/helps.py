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
from typing import Any, Final

import discord
from discord import app_commands
from discord.app_commands import locale_str
from discord.components import SelectOption
from discord.interactions import Interaction

from qingque.bot import QingqueClient
from qingque.i18n import PartialTranslate, get_i18n_discord

__all__ = ("qqhelps_main",)
_EMBED_COLOR: Final[int] = 3626589
_EMBED_ICON: Final[str] = "https://raw.githubusercontent.com/naoTimesdev/qingque-data/master/icon/character/1201.png"
_EMBED_URL: Final[str] = "https://github.com/naoTimesdev/qingque-gamba"


def _help_bind(t: PartialTranslate) -> discord.Embed:
    embed = discord.Embed(title=t("help.bind.title"), description=t("help.bind.desc"), color=_EMBED_COLOR)
    embed.add_field(name="/srbind", value=t("help.bind.srbind"), inline=False)
    embed.add_field(name="/srhoyobind", value=t("help.bind.srhoyobind"), inline=False)
    embed.set_author(name="Qingque", icon_url=_EMBED_ICON, url=_EMBED_URL)
    embed.set_footer(text=t("help.footer"))
    return embed


def _help_profiles(t: PartialTranslate) -> discord.Embed:
    embed = discord.Embed(title=t("help.profiles.title"), description=t("help.profiles.desc"), color=_EMBED_COLOR)
    embed.add_field(name="/srprofile", value=t("help.profiles.srprofile"), inline=False)
    embed.add_field(name="/srplayer", value=t("help.profiles.srplayer"), inline=False)
    embed.add_field(name="/srchronicle", value=t("help.profiles.srchronicle"), inline=False)
    embed.add_field(name="/srcharacters", value=t("help.profiles.srcharacters"), inline=False)
    embed.add_field(name="/srsimuniverse", value=t("help.profiles.srsimuniverse"), inline=False)
    embed.add_field(name="/srmoc", value=t("help.profiles.srmoc"), inline=False)
    embed.set_author(name="Qingque", icon_url=_EMBED_ICON, url=_EMBED_URL)
    embed.set_footer(text=t("help.footer"))
    return embed


def _help_rewards(t: PartialTranslate) -> discord.Embed:
    embed = discord.Embed(title=t("help.rewards.title"), description=t("help.rewards.desc"), color=_EMBED_COLOR)
    embed.add_field(name="/srdaily", value=t("help.rewards.srclaim"), inline=False)
    embed.add_field(name="/srredeem", value=t("help.rewards.srredeem"), inline=False)
    embed.set_author(name="Qingque", icon_url=_EMBED_ICON, url=_EMBED_URL)
    embed.set_footer(text=t("help.footer"))
    return embed


class HelpDropdown(discord.ui.Select):
    def __init__(self, t: PartialTranslate) -> None:
        self.t = t
        options = [
            SelectOption(label=t("help.bind.title"), description=t("help.bind.short_desc"), value="bind", emoji="🔑"),
            SelectOption(
                label=t("help.profiles.title"), description=t("help.profiles.short_desc"), value="profiles", emoji="🎆"
            ),
            SelectOption(
                label=t("help.rewards.title"), description=t("help.rewards.short_desc"), value="rewards", emoji="🎁"
            ),
        ]

        super().__init__(
            min_values=1,
            max_values=1,
            placeholder=t("help.placeholder"),
            options=options,
        )

    async def callback(self, interaction: Interaction[QingqueClient]) -> Any:
        if self.values[0] == "bind":
            await interaction.response.edit_message(embed=_help_bind(self.t))
        elif self.values[0] == "profiles":
            await interaction.response.edit_message(embed=_help_profiles(self.t))
        elif self.values[0] == "rewards":
            await interaction.response.edit_message(embed=_help_rewards(self.t))


class HelpView(discord.ui.View):
    _message: discord.InteractionMessage

    def __init__(self, t: PartialTranslate, *, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        self._dropdown = HelpDropdown(t)
        self.add_item(self._dropdown)

    async def on_timeout(self) -> None:
        self._dropdown.disabled = True
        await self._message.edit(view=self)

    async def start(self, initial: discord.Embed, inter: discord.InteractionMessage):
        self._message = inter
        await self._message.edit(embed=initial, view=self)


class HelpMenu(int, Enum):
    bind = 0
    profiles = 1
    rewards = 2


@app_commands.command(name="srhelp", description=locale_str("srhelp.desc"))
@app_commands.describe(help=locale_str("srhelp.initial_help_desc"))
async def qqhelps_main(inter: discord.Interaction, help: HelpMenu = HelpMenu.bind):
    t = get_i18n_discord(inter.locale)
    await inter.response.defer(ephemeral=True, thinking=True)
    view = HelpView(t)
    original_resp = await inter.original_response()
    match help:
        case HelpMenu.bind:
            await view.start(_help_bind(t), original_resp)
        case HelpMenu.profiles:
            await view.start(_help_profiles(t), original_resp)
        case HelpMenu.rewards:
            await view.start(_help_rewards(t), original_resp)
