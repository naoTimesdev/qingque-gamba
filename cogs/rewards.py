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

import discord
from discord import app_commands
from discord.app_commands import locale_str

from qingque.bot import QingqueClient
from qingque.hylab.models.errors import HYAlreadyClaimed, HYGeetestTriggered, HYInvalidCookies
from qingque.i18n import get_i18n_discord
from qingque.models.account_select import AccountSelectView
from qingque.models.persistence import QingqueProfile, QingqueProfileV2
from qingque.redisdb import RedisDatabase
from qingque.tooling import get_logger

__all__ = ("qqrewards_daily",)
logger = get_logger("cogs.rewards")


async def get_profile_from_persistent(discord_id: int, redis: RedisDatabase) -> QingqueProfileV2 | None:
    logger.info(f"Getting profile info for Discord ID {discord_id}")
    profile = await redis.get(f"qqgamba:profilev2:{discord_id}", type=QingqueProfileV2)
    if profile is None:
        legacy_profile = await redis.get(f"qqgamba:profile:{discord_id}", type=QingqueProfile)
        if legacy_profile is None:
            logger.warning(f"Discord ID {discord_id} haven't binded their UID yet.")
            return None
        logger.warning(f"Discord ID {discord_id} use legacy profile design, migrating...")
        profile = QingqueProfileV2.from_legacy(legacy_profile)
        await redis.set(f"qqgamba:profilev2:{discord_id}", profile)
        await redis.rm(f"qqgamba:profile:{discord_id}")
    return profile


@app_commands.command(name="srdaily", description=locale_str("srdaily.desc"))
async def qqrewards_daily(inter: discord.Interaction[QingqueClient]):
    t = get_i18n_discord(inter.locale)

    try:
        hoyoapi = inter.client.hoyoapi
    except RuntimeError:
        logger.warning("HYLab API is not enabled.")
        await inter.response.send_message(t("api_not_enabled"), ephemeral=True)
        return

    await inter.response.defer(ephemeral=True, thinking=True)

    original_message = await inter.original_response()
    profile = await get_profile_from_persistent(inter.user.id, inter.client.redis)
    if profile is None:
        return await original_message.edit(content=t("bind_uid"))
    if len(profile.games) == 0:
        return await original_message.edit(content=t("bind_uid"))

    if profile.hylab_id is None:
        logger.warning(f"Discord ID {inter.user.id} haven't binded their HoyoLab account yet.")
        return await original_message.edit(content=t("bind_hoyolab"))

    if profile.hylab_token is None:
        logger.warning(f"Discord ID {inter.user.id} binded their HoyoLab account but no token.")
        return await original_message.edit(content=t("bind_hoyolab_token"))

    if len(profile.games) > 1:
        select_account = AccountSelectView(profile.games, inter.locale, timeout=30)
        original_message = await original_message.edit(content=t("srchoices.ask_account"), view=select_account)
        await select_account.wait()

        if (error := select_account.error) is not None:
            logger.error(f"Error getting profile info for Discord ID {inter.user.id}: {error}", exc_info=error)
            error_message = str(error)
            await original_message.edit(content=t("exception", [f"```{error_message}```"]))
            return

        if select_account.account is None:
            return await original_message.edit(content=t("srchoices.timeout"))

        sel_uid = select_account.account.uid
    else:
        sel_uid = profile.games[0].uid

    try:
        await hoyoapi.claim_daily_reward(sel_uid, profile.hylab_id, hylab_token=profile.hylab_token)
    except HYGeetestTriggered:
        logger.error(f"Discord ID {inter.user.id} triggered Geetest.")
        return await original_message.edit(content=t("geetest_error"))
    except HYAlreadyClaimed:
        logger.warning(f"Discord ID {inter.user.id} already claimed daily reward.")
        return await original_message.edit(content=t("srdaily.already_claimed"))
    except HYInvalidCookies:
        logger.error(f"Discord ID {inter.user.id} has invalid cookies.")
        return await original_message.edit(content=t("invalid_token"))
    except Exception as e:
        logger.error(f"Error claiming daily reward for Discord ID {inter.user.id}: {e}", exc_info=e)
        error_message = str(e)
        return await original_message.edit(content=t("exception", [f"```{error_message}```"]))

    logger.info(f"Discord ID {inter.user.id} claimed daily reward.")
    await original_message.edit(content=t("srdaily.claimed"))
