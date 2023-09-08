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

import functools
from io import BytesIO

import discord
from discord import app_commands
from discord.app_commands import locale_str

from qingque.bot import QingqueClient
from qingque.extensions.files import FileBytes
from qingque.hylab.models.base import HYLanguage
from qingque.hylab.models.errors import HYDataNotPublic
from qingque.i18n import QingqueLanguage, get_i18n
from qingque.models.account_select import AccountSelectView
from qingque.models.embed_paging import EmbedPaginatedView
from qingque.models.persistence import QingqueProfile, QingqueProfileV2
from qingque.redisdb import RedisDatabase
from qingque.starrail.generator import StarRailMihomoCard
from qingque.starrail.generator.chronicles import StarRailChronicleNotesCard
from qingque.tooling import get_logger

__all__ = ("qqprofile_srprofile",)
logger = get_logger("cogs.profiles")
SRS_BASE = "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/"


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


@app_commands.command(name="srprofile", description=locale_str("srprofile.desc"))
@app_commands.describe(uid=locale_str("srprofile.uid_desc"))
async def qqprofile_srprofile(inter: discord.Interaction[QingqueClient], uid: int | None = None):
    mihomo = inter.client.mihomo
    lang = QingqueLanguage.from_discord(inter.locale)
    t = functools.partial(get_i18n().t, language=lang)

    await inter.response.defer(ephemeral=False, thinking=True)

    original_message = await inter.original_response()
    if uid is None:
        profile = await get_profile_from_persistent(inter.user.id, inter.client.redis)
        if profile is None:
            return await original_message.edit(content=t("bind_uid"))
        if len(profile.games) == 1:
            uid = profile.games[0].uid
        elif len(profile.games) == 0:
            return await original_message.edit(content=t("bind_uid"))
        else:
            select_account = AccountSelectView(profile.games, inter.locale, timeout=30)
            original_message = await original_message.edit(content=t("srchoices.ask_account"), view=select_account)
            await select_account.wait()

            if (error := select_account.error) is not None:
                logger.error(f"Error getting profile info for Discord ID {inter.user.id}: {error}")
                error_message = str(error)
                await original_message.edit(content=t("exception", [f"`{error_message}`"]))
                return

            if select_account.account is None:
                return await original_message.edit(content=t("srchoices.timeout"))

            uid = select_account.account.uid

    logger.info(f"Getting profile info for UID {uid}")
    try:
        data_player, _ = await mihomo.get_player(uid)
    except Exception as e:
        logger.error(f"Error getting profile info for UID {uid}: {e}")
        error_message = str(e)
        await original_message.edit(content=t("exception", [f"`{error_message}`"]))
        return
    logger.info(f"Getting profile card for UID {uid}")

    embeds: list[discord.Embed] = []
    files: list[discord.File] = []
    for idx, character in enumerate(data_player.characters, 1):
        card_char = StarRailMihomoCard(character, data_player.player, language=lang)
        logger.info(f"Generating character {character.name} profile card for UID {uid}")
        card_data = await card_char.create()

        logger.info(f"Adding character {character.name} profile card for UID {uid}")
        filename = f"{data_player.player.id}_{idx:02d}_{character.id}.png"
        file = FileBytes(card_data, filename=filename)
        embed = discord.Embed(title=t("character_header", [character.name, f"{character.level:02d}"]))
        description = []
        progression = data_player.player.progression
        if progression.achivements > 0:
            description.append(f"**{t('achivements')}**: {progression.achivements}")
        if progression.light_cones > 0:
            description.append(f"**{t('light_cones')}**: {progression.light_cones}")
        if progression.simulated_universe.value > 0:
            rogue_world = t("rogue_world", [str(progression.simulated_universe.value)])
            description.append(f"**{t('rogue')}**: {rogue_world}")
        forgotten_hall = progression.forgotten_hall
        if forgotten_hall.finished_floor > 0:
            abyss_floor = t("moc_floor", [str(forgotten_hall.finished_floor)])
            description.append(f"**{t('abyss')}**: {abyss_floor}")
        if forgotten_hall.moc_finished_floor > 0:
            abyss_moc_floor = t("moc_floor", [str(forgotten_hall.moc_finished_floor)])
            description.append(f"**{t('abyss_hard')}**: {abyss_moc_floor}")

        embed.description = "\n".join(description)
        embed.set_image(url=f"attachment://{filename}")
        embed.set_author(
            name=data_player.player.name,
            icon_url=f"{SRS_BASE}{data_player.player.avatar.icon_url}",
        )
        embeds.append(embed)
        files.append(file)

    logger.info("Sending to Discord...")
    pagination_view = EmbedPaginatedView(embeds, inter.user.id, files)
    await pagination_view.start(inter, message=original_message)


@app_commands.command(name="srchronicle", description=locale_str("srchronicle.desc"))
async def qqprofile_srchronicle(inter: discord.Interaction[QingqueClient]):
    lang = QingqueLanguage.from_discord(inter.locale)
    t = functools.partial(get_i18n().t, language=lang)

    try:
        hoyoapi = inter.client.hoyoapi
    except RuntimeError:
        logger.warning("HYLab API is not enabled.")
        await inter.response.send_message(t("api_not_enabled"), ephemeral=True)
        return

    await inter.response.defer(ephemeral=False, thinking=True)

    original_message = await inter.original_response()
    profile = await get_profile_from_persistent(inter.user.id, inter.client.redis)
    if profile is None:
        return await original_message.edit(content=t("bind_uid"))
    if len(profile.games) == 0:
        return await original_message.edit(content=t("bind_uid"))

    if profile.hylab_id is None:
        logger.warning(f"Discord ID {inter.user.id} haven't binded their HoyoLab account yet.")
        return await original_message.edit(content=t("bind_hoyolab"))

    if len(profile.games) > 1:
        select_account = AccountSelectView(profile.games, inter.locale, timeout=30)
        original_message = await original_message.edit(content=t("srchoices.ask_account"), view=select_account)
        await select_account.wait()

        if (error := select_account.error) is not None:
            logger.error(f"Error getting profile info for Discord ID {inter.user.id}: {error}")
            error_message = str(error)
            await original_message.edit(content=t("exception", [f"`{error_message}`"]))
            return

        if select_account.account is None:
            return await original_message.edit(content=t("srchoices.timeout"))

        sel_uid = select_account.account.uid
    else:
        sel_uid = profile.games[0].uid

    logger.info(f"Getting profile overview for UID {sel_uid}")
    try:
        hoyo_overview = await hoyoapi.get_battle_chronicles_overview(
            sel_uid,
            hylab_id=profile.hylab_id,
            hylab_token=profile.hylab_token,
            lang=HYLanguage(lang.value.lower()),
        )
    except HYDataNotPublic:
        logger.warning(f"UID {sel_uid} data is not public.")
        await original_message.edit(content=t("hoyolab_public"))
        return
    except Exception as e:
        logger.error(f"Error getting profile info for UID {sel_uid}: {e}")
        error_message = str(e)
        await original_message.edit(content=t("exception", [f"`{error_message}`"]))
        return
    logger.info(f"Getting profile real-time notes for UID {sel_uid}")
    try:
        hoyo_realtime = await hoyoapi.get_battle_chronicles_notes(
            sel_uid,
            hylab_id=profile.hylab_id,
            hylab_token=profile.hylab_token,
            lang=HYLanguage(lang.value.lower()),
        )
    except HYDataNotPublic:
        logger.warning(f"UID {sel_uid} data is not public.")
        await original_message.edit(content=t("hoyolab_public"))
        return
    except Exception as e:
        logger.error(f"Error getting profile info for UID {sel_uid}: {e}")
        error_message = str(e)
        await original_message.edit(content=t("exception", [f"`{error_message}`"]))
        return

    if hoyo_realtime is None:
        logger.warning(f"UID {sel_uid} data is not available.")
        await original_message.edit(content=t("hoyolab_unavailable"))
        return

    if hoyo_overview.overview is None:
        logger.warning(f"UID {sel_uid} data is not available. (Overview)")
        await original_message.edit(content=t("hoyolab_unavailable"))
        return
    if hoyo_overview.user_info is None:
        logger.warning(f"UID {sel_uid} data is not available. (User Info)")
        await original_message.edit(content=t("hoyolab_unavailable"))
        return

    embed = discord.Embed(title=t("chronicle_titles.overview"))
    embed.set_author(name=hoyo_overview.user_info.name, icon_url=hoyo_overview.overview.avatar_url)

    descriptions = []
    tb_power_txt = f"**{t('tb_power')}**: {hoyo_realtime.stamina:,}/{hoyo_realtime.max_stamina:,}"
    if hoyo_realtime.stamina_recover_in > 0:
        recover_in = int(round(hoyo_realtime.stamina_reset_at))
        recover_txt = t("tb_power_recover", [f"<t:{recover_in}:R>"])
        tb_power_txt += f" {recover_txt}"
    descriptions.append(tb_power_txt)
    if hoyo_realtime.reserve_stamina > 0:
        descriptions.append(f"**{t('tb_power_reserve')}**: {hoyo_realtime.reserve_stamina:,}")
    descriptions.append(
        f"**{t('daily_quest')}**: {hoyo_realtime.training_score:,}/{hoyo_realtime.training_max_score:,}"
    )
    descriptions.append(
        f"**{t('rogue')}**: {hoyo_realtime.simulated_universe_score:,}/"
        f"{hoyo_realtime.simulated_universe_max_score:,}"
    )
    descriptions.append(f"**{t('echo_of_war')}**: {hoyo_realtime.eow_available:,}/{hoyo_realtime.eow_limit:,}")
    embed.description = "\n".join(descriptions)

    logger.info(f"Generating profile card for {sel_uid}...")
    card_char = StarRailChronicleNotesCard(hoyo_overview, hoyo_realtime)
    card_data = await card_char.create()

    card_io = BytesIO(card_data)
    card_file = discord.File(card_io, f"{sel_uid}_ChroniclesOverview.png")
    embed.set_image(url=f"attachment://{card_file.filename}")

    for idx, assignment in enumerate(hoyo_realtime.assignments, 1):
        assign_values = []
        assign_values.append(f"**{t('assignment.name')}**: {assignment.name}")
        assign_stat = f"**{t('assignment.status.title')}**: "
        if assignment.status.is_ongoing():
            assign_stat += t("assignment.status.ongoing")
        else:
            assign_stat += t("assignment.status.finished")
        assign_values.append(assign_stat)
        relative_done = int(round(hoyo_realtime.requested_at + assignment.time_left))
        assign_values.append(f"**{t('assignment.finish')}**: <t:{relative_done}:f>")
        embed.add_field(name=f"{t('assignment.title', [str(idx)])}", value="\n".join(assign_values), inline=True)

    logger.info("Sending to Discord...")
    await original_message.edit(content=None, embed=embed, attachments=[card_file])
