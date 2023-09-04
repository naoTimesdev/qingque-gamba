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
from qingque.models.embed_paging import EmbedPaginatedView
from qingque.models.persistence import QingqueProfile
from qingque.starrail.generator import StarRailMihomoCard
from qingque.starrail.generator.chronicles import StarRailChronicleNotesCard
from qingque.tooling import get_logger

__all__ = ("qqprofile_srprofile",)
logger = get_logger("cogs.profiles")
SRS_BASE = "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/"


@app_commands.command(name="srprofile", description=locale_str("srprofile.desc"))
@app_commands.describe(uid=locale_str("srprofile.uid_desc"))
async def qqprofile_srprofile(inter: discord.Interaction[QingqueClient], uid: int | None = None):
    mihomo = inter.client.mihomo
    lang = QingqueLanguage.from_discord(inter.locale)
    t = functools.partial(get_i18n().t, language=lang)

    if uid is None:
        logger.info(f"Getting profile info for Discord ID {inter.user.id}")
        profile = await inter.client.redis.get(f"qqgamba:profile:{inter.user.id}", type=QingqueProfile)
        if profile is None:
            logger.warning(f"Discord ID {inter.user.id} haven't binded their UID yet.")
            await inter.response.send_message(t("bind_uid"), ephemeral=True)
            return

        uid = profile.uid

    await inter.response.defer(ephemeral=False, thinking=True)
    original_message = await inter.original_response()
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

    logger.info(f"Getting profile info for Discord ID {inter.user.id}")
    profile = await inter.client.redis.get(f"qqgamba:profile:{inter.user.id}", type=QingqueProfile)
    if profile is None:
        logger.warning(f"Discord ID {inter.user.id} haven't binded their UID yet.")
        await inter.response.send_message(t("bind_uid"), ephemeral=True)
        return

    if profile.hylab_id is None:
        logger.warning(f"Discord ID {inter.user.id} haven't binded their HoyoLab account yet.")
        await inter.response.send_message(t("bind_hoyolab"), ephemeral=True)

    uid = profile.uid
    await inter.response.defer(ephemeral=False, thinking=True)
    original_message = await inter.original_response()
    logger.info(f"Getting profile overview for UID {uid}")
    try:
        hoyo_overview = await hoyoapi.get_battle_chronicles_overview(
            profile.uid,
            hylab_id=profile.hylab_id,
            hylab_token=profile.hylab_token,
            lang=HYLanguage(lang.value.lower()),
        )
    except HYDataNotPublic:
        logger.warning(f"UID {uid} data is not public.")
        await original_message.edit(content=t("hoyolab_public"))
        return
    except Exception as e:
        logger.error(f"Error getting profile info for UID {uid}: {e}")
        error_message = str(e)
        await original_message.edit(content=t("exception", [f"`{error_message}`"]))
        return
    logger.info(f"Getting profile real-time notes for UID {uid}")
    try:
        hoyo_realtime = await hoyoapi.get_battle_chronicles_notes(
            profile.uid,
            hylab_id=profile.hylab_id,
            hylab_token=profile.hylab_token,
            lang=HYLanguage(lang.value.lower()),
        )
    except HYDataNotPublic:
        logger.warning(f"UID {uid} data is not public.")
        await original_message.edit(content=t("hoyolab_public"))
        return
    except Exception as e:
        logger.error(f"Error getting profile info for UID {uid}: {e}")
        error_message = str(e)
        await original_message.edit(content=t("exception", [f"`{error_message}`"]))
        return

    if hoyo_realtime is None:
        logger.warning(f"UID {uid} data is not available.")
        await original_message.edit(content=t("hoyolab_unavailable"))
        return

    if hoyo_overview.overview is None:
        logger.warning(f"UID {uid} data is not available. (Overview)")
        await original_message.edit(content=t("hoyolab_unavailable"))
        return
    if hoyo_overview.user_info is None:
        logger.warning(f"UID {uid} data is not available. (User Info)")
        await original_message.edit(content=t("hoyolab_unavailable"))
        return

    embed = discord.Embed(title=t("chronicle_titles.overview"))
    embed.set_author(name=hoyo_overview.user_info.name, icon_url=hoyo_overview.overview.avatar_url)

    descriptions = []
    tb_power_txt = f"**{t('tb_power')}**: {hoyo_realtime.stamina:,}/{hoyo_realtime.max_stamina:,}"
    if hoyo_realtime.stamina_recover_in > 0:
        recover_txt = t("tb_power_recover", [f"<t:{hoyo_realtime.stamina_reset_at}:R>"])
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

    logger.info(f"Generating profile card for {uid}...")
    card_char = StarRailChronicleNotesCard(hoyo_overview, hoyo_realtime)
    card_data = await card_char.create()

    card_io = BytesIO(card_data)
    card_file = discord.File(card_io, f"{uid}_ChroniclesOverview.png")
    embed.set_image(url=f"attachment://{card_file.filename}")

    for idx, assignment in enumerate(hoyo_realtime.assignments, 1):
        assign_values = []
        assign_values.append(f"**{t('assignment.name')}**: {assignment.name}")
        assign_stat = f"**{t('assignment.status')}**: "
        if assignment.status.is_ongoing():
            assign_stat += t("assignment.status.ongoing")
        else:
            assign_stat += t("assignment.status.finished")
        assign_values.append(assign_stat)
        relative_done = hoyo_realtime.requested_at + assignment.time_left
        assign_values.append(f"**{t('assignment.finish')}**: <t:{relative_done}:R>")
        embed.add_field(name=f"{t('assignment.title')} {idx}", value="\n".join(assign_values), inline=True)

    logger.info("Sending to Discord...")
    await original_message.edit(content=None, embed=embed, attachments=[card_file])
