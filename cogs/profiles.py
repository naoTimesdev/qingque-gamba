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

from io import BytesIO

import discord
from discord import app_commands

from qingque.bot import QingqueClient
from qingque.extensions.files import FileBytes
from qingque.hylab.models.errors import HYDataNotPublic
from qingque.models.embed_paging import EmbedPaginatedView
from qingque.models.persistence import QingqueProfile
from qingque.starrail.generator import StarRailMihomoCard
from qingque.starrail.generator.chronicles import StarRailChronicleNotesCard
from qingque.tooling import get_logger

__all__ = ("qqprofile_srprofile",)
logger = get_logger("cogs.profiles")
SRS_BASE = "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/"


@app_commands.command(name="srprofile", description="See your profile card.")
@app_commands.describe(uid="Your in-game UID, if not provided will use the binded UID.")
async def qqprofile_srprofile(inter: discord.Interaction[QingqueClient], uid: int | None = None):
    mihomo = inter.client.mihomo

    if uid is None:
        logger.info(f"Getting profile info for Discord ID {inter.user.id}")
        profile = await inter.client.redis.get(f"qqgamba:profile:{inter.user.id}", type=QingqueProfile)
        if profile is None:
            logger.warning(f"Discord ID {inter.user.id} haven't binded their UID yet.")
            await inter.response.send_message("You haven't binded your UID yet.", ephemeral=True)
            return

        uid = profile.uid

    await inter.response.defer(ephemeral=False, thinking=True)
    original_message = await inter.original_response()
    logger.info(f"Getting profile info for UID {uid}")
    try:
        data_player, language = await mihomo.get_player(uid)
    except Exception as e:
        logger.error(f"Error getting profile info for UID {uid}: {e}")
        error_message = str(e)
        await original_message.edit(content=f"Something went wrong, please try again later.\n`{error_message}`")
        return
    logger.info(f"Getting profile card for UID {uid}")

    embeds: list[discord.Embed] = []
    files: list[discord.File] = []
    for idx, character in enumerate(data_player.characters, 1):
        card_char = StarRailMihomoCard(character, data_player.player, language=language)
        logger.info(f"Generating character {character.name} profile card for UID {uid}")
        card_data = await card_char.create()

        logger.info(f"Adding character {character.name} profile card for UID {uid}")
        filename = f"{data_player.player.id}_{idx:02d}_{character.id}.png"
        file = FileBytes(card_data, filename=filename)
        embed = discord.Embed(title=f"{character.name} (Lv {character.level:02d})")
        description = []
        progression = data_player.player.progression
        if progression.achivements > 0:
            description.append(f"**Achievements**: {progression.achivements}")
        if progression.light_cones > 0:
            description.append(f"**Light Cones**: {progression.light_cones}")
        if progression.simulated_universe.value > 0:
            description.append(f"**Simulated Universe**: World {progression.simulated_universe.value}")
        forgotten_hall = progression.forgotten_hall
        if forgotten_hall.finished_floor > 0:
            description.append(f"**Forgotten Hall**: Floor {forgotten_hall.finished_floor}")
        if forgotten_hall.moc_finished_floor > 0:
            description.append(f"**Memory of Chaos**: Floor {forgotten_hall.moc_finished_floor}")

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


@app_commands.command(name="srchronicle", description="See your profile chronicle from HoyoLab.")
async def qqprofile_srchronicle(inter: discord.Interaction[QingqueClient]):
    try:
        hoyoapi = inter.client.hoyoapi
    except RuntimeError:
        logger.warning("HYLab API is not enabled.")
        await inter.response.send_message("API is not enabled.", ephemeral=True)
        return

    logger.info(f"Getting profile info for Discord ID {inter.user.id}")
    profile = await inter.client.redis.get(f"qqgamba:profile:{inter.user.id}", type=QingqueProfile)
    if profile is None:
        logger.warning(f"Discord ID {inter.user.id} haven't binded their UID yet.")
        await inter.response.send_message("You haven't binded your UID yet.", ephemeral=True)
        return

    if profile.hylab_id is None:
        logger.warning(f"Discord ID {inter.user.id} haven't binded their HoyoLab account yet.")
        await inter.response.send_message("You haven't binded your HoyoLab account yet.", ephemeral=True)

    uid = profile.uid
    await inter.response.defer(ephemeral=False, thinking=True)
    original_message = await inter.original_response()
    logger.info(f"Getting profile overview for UID {uid}")
    try:
        hoyo_overview = await hoyoapi.get_battle_chronicles_overview(
            profile.uid, hylab_id=profile.hylab_id, hylab_token=profile.hylab_token
        )
    except HYDataNotPublic:
        logger.warning(f"UID {uid} data is not public.")
        await original_message.edit(content="Your HoyoLab data is not public, please make it public!")
        return
    except Exception as e:
        logger.error(f"Error getting profile info for UID {uid}: {e}")
        error_message = str(e)
        await original_message.edit(content=f"Something went wrong, please try again later.\n`{error_message}`")
        return
    logger.info(f"Getting profile real-time notes for UID {uid}")
    try:
        hoyo_realtime = await hoyoapi.get_battle_chronicles_notes(
            profile.uid, hylab_id=profile.hylab_id, hylab_token=profile.hylab_token
        )
    except HYDataNotPublic:
        logger.warning(f"UID {uid} data is not public.")
        await original_message.edit(content="Your HoyoLab data is not public, please make it public!")
        return
    except Exception as e:
        logger.error(f"Error getting profile info for UID {uid}: {e}")
        error_message = str(e)
        await original_message.edit(content=f"Something went wrong, please try again later.\n`{error_message}`")
        return

    if hoyo_realtime is None:
        logger.warning(f"UID {uid} data is not available.")
        await original_message.edit(content="Your HoyoLab data is not available, please make it public if you haven't!")
        return

    if hoyo_overview.overview is None:
        logger.warning(f"UID {uid} data is not available. (Overview)")
        await original_message.edit(content="Your HoyoLab data is not available, please make it public if you haven't!")
        return
    if hoyo_overview.user_info is None:
        logger.warning(f"UID {uid} data is not available. (User Info)")
        await original_message.edit(content="Your HoyoLab data is not available, please make it public if you haven't!")
        return

    embed = discord.Embed(title="Battle Chronicle")
    embed.set_author(name=hoyo_overview.user_info.name, icon_url=hoyo_overview.overview.avatar_url)

    descriptions = []
    tb_power_txt = f"**Trailblaze Power**: {hoyo_realtime.stamina:,}/{hoyo_realtime.max_stamina:,}"
    if hoyo_realtime.stamina_recover_in > 0:
        tb_power_txt += f" (Recover in <t:{hoyo_realtime.stamina_reset_at}:R>)"
    descriptions.append(tb_power_txt)
    if hoyo_realtime.reserve_stamina > 0:
        descriptions.append(f"**Reserve Power**: {hoyo_realtime.reserve_stamina:,}")
    descriptions.append(f"**Daily Training**: {hoyo_realtime.training_score:,}/{hoyo_realtime.training_max_score:,}")
    descriptions.append(
        f"**Simulated Universe**: {hoyo_realtime.simulated_universe_score:,}/"
        f"{hoyo_realtime.simulated_universe_max_score:,}"
    )
    descriptions.append(f"**Echo of War**: {hoyo_realtime.eow_available:,}/{hoyo_realtime.eow_limit:,}")
    embed.description = "\n".join(descriptions)

    logger.info(f"Generating profile card for {uid}...")
    card_char = StarRailChronicleNotesCard(hoyo_overview, hoyo_realtime)
    card_data = await card_char.create()

    card_io = BytesIO(card_data)
    card_file = discord.File(card_io, f"{uid}_ChroniclesOverview.png")
    embed.set_image(url=f"attachment://{card_file.filename}")

    for idx, assignment in enumerate(hoyo_realtime.assignments, 1):
        assign_values = []
        assign_values.append(f"**Name**: {assignment.name}")
        assign_values.append(f"**Status**: {assignment.status.value}")
        relative_done = hoyo_realtime.requested_at + assignment.time_left
        assign_values.append(f"**Finish at**: <t:{relative_done}:R>")
        embed.add_field(name=f"Assignment {idx}", value="\n".join(assign_values), inline=True)

    logger.info("Sending to Discord...")
    await original_message.edit(content=None, embed=embed, attachments=[card_file])
