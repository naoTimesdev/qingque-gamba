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

import discord
from discord import app_commands
from discord.app_commands import locale_str

from qingque.bot import QingqueClient
from qingque.hylab.models.errors import HYLabException
from qingque.i18n import get_i18n_discord
from qingque.models.confirm import ConfirmView
from qingque.models.persistence import (
    QingqueProfile,
    QingqueProfileV2,
    QingqueProfileV2Game,
    QingqueProfileV2GameKind,
)
from qingque.tooling import get_logger

__all__ = (
    "qqpersist_srbind",
    "qqpersist_srhoyobind",
)
logger = get_logger("cogs.persistent")


class HoyoBindAction(int, Enum):
    Bind = 1
    Remove = 2
    Cancel = -999


class HoyoBindActionView(discord.ui.View):
    def __init__(self, *, timeout: float | None = 180):
        super().__init__(timeout=timeout)

        self._action: HoyoBindAction | None = None

    @property
    def action(self) -> HoyoBindAction | None:
        return self._action

    @discord.ui.button(label="Bind", style=discord.ButtonStyle.primary)
    async def bind(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self._action = HoyoBindAction.Bind
        self.stop()

    @discord.ui.button(label="Remove", style=discord.ButtonStyle.danger)
    async def remove(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self._action = HoyoBindAction.Remove
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self._action = HoyoBindAction.Cancel
        self.stop()


@app_commands.command(name="srbind", description=locale_str("srbind.desc"))
@app_commands.describe(uid=locale_str("srbind.uid_desc"))
async def qqpersist_srbind(inter: discord.Interaction[QingqueClient], uid: int):
    t = get_i18n_discord(inter.locale)
    discord_id = inter.user.id
    logger.info(f"Binding UID {uid} to {discord_id}")

    profile = await inter.client.redis.get(f"qqgamba:profilev2:{discord_id}", type=QingqueProfileV2)
    if profile is None:
        legacy_profile = await inter.client.redis.get(f"qqgamba:profile:{discord_id}", type=QingqueProfile)
        if legacy_profile is not None:
            logger.info(f"UID {uid} already binded to {discord_id} via legacy profile, migrating...")
            profile = QingqueProfileV2.from_legacy(legacy_profile)
            # Save it first, delete the legacy profile later
            await inter.client.redis.set(f"qqgamba:profilev2:{discord_id}", profile)
            await inter.client.redis.rm(f"qqgamba:profile:{discord_id}")
        else:
            profile = QingqueProfileV2(
                id=str(discord_id),
                games=[],
            )

    uid_ingame = False
    if profile.games:
        for game in profile.games:
            if game.uid == uid:
                logger.info(f"UID {uid} already binded to {discord_id} via profile, skipping...")
                uid_ingame = True
                break

    view = HoyoBindActionView()
    view.bind.disabled = uid_ingame
    view.remove.disabled = not uid_ingame
    await inter.response.send_message(content=t("srbind.ask_action", {"uid": str(uid)}), view=view, ephemeral=True)
    original_response = await inter.original_response()
    await view.wait()

    if view.action is None:
        return await original_response.edit(content=t("srbind.timeout"), view=None)
    elif view.action == HoyoBindAction.Bind:
        # Bind
        if uid_ingame:
            return await original_response.edit(content=t("srbind.already_bind"))

        profile.games.append(QingqueProfileV2Game(kind=QingqueProfileV2GameKind.StarRail, uid=uid))

        await inter.client.redis.set(f"qqgamba:profilev2:{discord_id}", profile)
        await original_response.edit(content=t("srbind.binded", {"uid": str(uid)}), view=None)
    elif view.action == HoyoBindAction.Remove:
        # Remove
        if not uid_ingame:
            return await original_response.edit(content=t("srbind.not_bind"))
        profile.games = [game for game in profile.games if game.uid != uid]

        await inter.client.redis.set(f"qqgamba:profilev2:{discord_id}", profile)
        await original_response.edit(content=t("srbind.removed", {"uid": str(uid)}), view=None)
    elif view.action == HoyoBindAction.Cancel:
        # Cancel
        await original_response.edit(content=t("srbind.cancelled"), view=None)


@app_commands.command(name="srhoyobind", description=locale_str("srhoyobind.desc"))
@app_commands.describe(hoyo_id=locale_str("srhoyobind.desc_id"))
@app_commands.describe(hoyo_token=locale_str("srhoyobind.desc_token"))
@app_commands.describe(hoyo_cookie=locale_str("srhoyobind.desc_cookie_token"))
async def qqpersist_srhoyobind(
    inter: discord.Interaction[QingqueClient],
    hoyo_id: int,
    hoyo_token: str,
    hoyo_cookie: str | None = None,
):
    discord_id = inter.user.id
    t = get_i18n_discord(inter.locale)

    try:
        hoyoapi = inter.client.hoyoapi
    except RuntimeError:
        logger.warning("HYLab API is not enabled.")
        await inter.response.send_message(t("api_not_enabled"), ephemeral=True)
        return

    profile = await inter.client.redis.get(f"qqgamba:profilev2:{discord_id}", type=QingqueProfileV2)
    if profile is None:
        legacy_profile = await inter.client.redis.get(f"qqgamba:profile:{discord_id}", type=QingqueProfile)
        if legacy_profile is None:
            return await inter.response.send_message(content=t("srhoyobind.bind_first"), ephemeral=True)
        logger.info(f"Discord ID {discord_id} already binded via legacy profile, migrating...")
        profile = QingqueProfileV2.from_legacy(legacy_profile)
        # Save it first, delete the legacy profile later
        await inter.client.redis.set(f"qqgamba:profilev2:{discord_id}", profile)
        await inter.client.redis.rm(f"qqgamba:profile:{discord_id}")
    if len(profile.games) < 1:
        return await inter.response.send_message(content=t("srhoyobind.bind_first"), ephemeral=True)

    await inter.response.defer(ephemeral=True, thinking=True)
    response = await inter.original_response()
    if profile.hylab_id is not None:
        view = ConfirmView()
        await response.edit(content=t("srhoyobind.already_bind"), view=view)
        await view.wait()

        if view is None:
            return await response.edit(content=t("srhoyobind.timeout"), view=None)
        elif view.value is False:
            return await response.edit(content=t("srhoyobind.cancelled"), view=None)

    profile.hylab_id = hoyo_id
    profile.hylab_token = hoyo_token
    profile.hylab_cookie = hoyo_cookie

    # Test if the token is valid
    first_uid = profile.games[0].uid
    try:
        logger.info(f"Testing HYLab token for UID {first_uid}...")
        await hoyoapi.get_battle_chronicles_overview(
            first_uid,
            hylab_id=hoyo_id,
            hylab_token=hoyo_token,
            hylab_cookie=hoyo_cookie,
        )
    except HYLabException as e:
        logger.error(f"Failed to bind UID {first_uid} to HYLab ID {hoyo_id}: {e}", exc_info=e)
        return await response.edit(content=t("srhoyobind.invalid_token"))
    except Exception as exc:
        logger.error(f"Error getting profile overview for UID {first_uid}: {exc}")
        error_message = str(exc)
        await response.edit(content=t("exception", [f"`{error_message}`"]))
        return

    await inter.client.redis.set(f"qqgamba:profilev2:{discord_id}", profile)
    await response.edit(content=t("srhoyobind.binded"), view=None)
