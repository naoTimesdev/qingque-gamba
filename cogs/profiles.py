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

import asyncio
import functools
from datetime import timezone
from io import BytesIO
from typing import TYPE_CHECKING, Any, Coroutine, Final

import discord
from discord import app_commands
from discord.app_commands import locale_str

from qingque.bot import QingqueClient
from qingque.extensions.files import FileBytes
from qingque.hylab.models.base import HYLanguage
from qingque.hylab.models.errors import HYDataNotPublic
from qingque.hylab.models.forgotten_hall import ChronicleFHFloor, ChronicleForgottenHall
from qingque.hylab.models.simuniverse import (
    ChronicleRogueLocustDetailRecord,
    ChronicleRogueLocustOverview,
    ChronicleRogueOverview,
    ChronicleRoguePeriodRun,
    ChronicleRogueUserInfo,
)
from qingque.i18n import PartialTranslate, QingqueLanguage, get_i18n, get_i18n_discord, get_roman_numeral
from qingque.mihomo.models.characters import Character
from qingque.mihomo.models.player import PlayerInfo
from qingque.models.account_select import AccountSelectView
from qingque.models.embed_paging import EmbedPagingSelectView, PagingChoice
from qingque.models.persistence import QingqueProfile, QingqueProfileV2
from qingque.redisdb import RedisDatabase
from qingque.starrail.generator import StarRailMihomoCard
from qingque.starrail.generator.characters import StarRailCharactersCard
from qingque.starrail.generator.chronicles import StarRailChronicleNotesCard
from qingque.starrail.generator.mihomo import get_mihomo_dominant_color
from qingque.starrail.generator.moc import StarRailMoCCard
from qingque.starrail.generator.player import StarRailPlayerCard
from qingque.starrail.generator.simuniverse import StarRailSimulatedUniverseCard
from qingque.starrail.loader import SRSDataLoader
from qingque.tooling import get_logger
from qingque.utils import strip_unity_rich_text

if TYPE_CHECKING:
    from qingque.starrail.scoring import RelicScoring

__all__ = (
    "qqprofile_srprofile",
    "qqprofile_srchronicle",
    "qqprofile_srrogue",
)
logger = get_logger("cogs.profiles")
SRS_BASE = "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/"
_COMMON_FOREGROUND: Final[discord.Colour] = discord.Colour.from_rgb(219, 194, 145)
_CHAR_EMOTES: Final[list[str]] = ["🌟", "1️⃣", "2️⃣", "3️⃣"]


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


async def _batch_gen_player_card(
    idx: int,
    player: PlayerInfo,
    character: Character,
    t: PartialTranslate,
    language: QingqueLanguage,
    loader: SRSDataLoader,
    scorer: RelicScoring,
    *,
    detailed: bool = False,
) -> PagingChoice:
    logger.info(f"Generating character {character.name} profile card for UID {player.id}")
    card_char = StarRailMihomoCard(
        character,
        player,
        language=language,
        loader=loader,
        relic_scorer=scorer,
    )
    card_data = await card_char.create(hide_credits=True, detailed=detailed)

    logger.info(f"Adding character {character.name} profile card for UID {player.id}")
    filename = f"{player.id}_{idx:02d}_{character.id}.QingqueBot.png"
    file = FileBytes(card_data, filename=filename)
    char_color = get_mihomo_dominant_color(character.id)
    char_disc_color = discord.Colour.from_rgb(*char_color) if char_color is not None else None
    char_header = t("character_header", [character.name, f"{character.level:02d}"])
    embed = discord.Embed(title=char_header, colour=char_disc_color)
    description = []
    progression = player.progression
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

    try:
        em_emote = _CHAR_EMOTES[idx]
    except IndexError:
        em_emote = None

    embed.description = "\n".join(description)
    embed.set_image(url=f"attachment://{filename}")
    embed.set_author(
        name=player.name,
        icon_url=f"{SRS_BASE}{player.avatar.icon_url}",
    )
    return PagingChoice(title=char_header, embed=embed, file=file, emoji=em_emote)


@app_commands.command(name="srprofile", description=locale_str("srprofile.desc"))
@app_commands.describe(uid=locale_str("srprofile.uid_desc"), detailed=locale_str("srprofile.detailed_desc"))
async def qqprofile_srprofile(
    inter: discord.Interaction[QingqueClient], uid: int | None = None, detailed: bool = False
):
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
                await original_message.edit(content=t("exception", [f"```{error_message}```"]))
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
        await original_message.edit(content=t("exception", [f"```{error_message}```"]))
        return
    logger.info(f"Getting profile card for UID {uid}")

    if not data_player.characters:
        return await original_message.edit(content=t("srprofile.no_characters"))

    task_creation = [
        asyncio.create_task(
            _batch_gen_player_card(
                idx,
                data_player.player,
                character,
                t,
                lang,
                inter.client.get_srs(lang),
                inter.client.relic_scorer,
                detailed=detailed,
            ),
            name=f"srprofile_{inter.created_at.timestamp():.0f}_{character.id}_{uid}",
        )
        for idx, character in enumerate(data_player.characters)
    ]
    try:
        profile_choices: list[PagingChoice] = await asyncio.gather(*task_creation)
    except Exception as e:
        logger.error(f"Error generating profile card for UID {uid}: {e}", exc_info=e)
        await original_message.edit(content=t("exception", [f"```{e!s}```"]))
        return

    logger.info("Sending to Discord...")
    pagination_view = EmbedPagingSelectView(profile_choices, inter.locale, user_id=inter.user.id)
    await pagination_view.start(original_message)


@app_commands.command(name="srplayer", description=locale_str("srplayer.desc"))
@app_commands.describe(uid=locale_str("srplayer.uid_desc"))
async def qqprofile_srplayer(inter: discord.Interaction[QingqueClient], uid: int | None = None):
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
                await original_message.edit(content=t("exception", [f"```{error_message}```"]))
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
        await original_message.edit(content=t("exception", [f"```{error_message}```"]))
        return
    logger.info(f"Getting profile card for UID {uid}")

    generator = StarRailPlayerCard(data_player, language=lang, loader=inter.client.get_srs(lang))
    card_bytes = await generator.create()

    player_io = BytesIO(card_bytes)
    player_io.seek(0)
    player_file = discord.File(player_io, filename=f"{uid}.QingqueBot.png")

    logger.info("Sending to Discord...")
    await original_message.edit(attachments=[player_file])


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
            await original_message.edit(content=t("exception", [f"```{error_message}```"]))
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
            hylab_mid_token=profile.hylab_mid_token,
            lang=HYLanguage(lang.value.lower()),
        )
    except HYDataNotPublic:
        logger.warning(f"UID {sel_uid} data is not public.")
        await original_message.edit(content=t("hoyolab_public"))
        return
    except Exception as e:
        logger.error(f"Error getting profile info for UID {sel_uid}: {e}")
        error_message = str(e)
        await original_message.edit(content=t("exception", [f"```{error_message}```"]))
        return
    logger.info(f"Getting profile real-time notes for UID {sel_uid}")
    try:
        hoyo_realtime = await hoyoapi.get_battle_chronicles_notes(
            sel_uid,
            hylab_id=profile.hylab_id,
            hylab_token=profile.hylab_token,
            hylab_mid_token=profile.hylab_mid_token,
            lang=HYLanguage(lang.value.lower()),
        )
    except HYDataNotPublic:
        logger.warning(f"UID {sel_uid} data is not public.")
        await original_message.edit(content=t("hoyolab_public"))
        return
    except Exception as e:
        logger.error(f"Error getting profile info for UID {sel_uid}: {e}")
        error_message = str(e)
        await original_message.edit(content=t("exception", [f"```{error_message}```"]))
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

    embed = discord.Embed(title=t("chronicle_titles.overview"), colour=_COMMON_FOREGROUND)
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

    loader = inter.client.get_srs(lang)

    logger.info(f"Generating profile card for {sel_uid}...")
    card_char = StarRailChronicleNotesCard(
        hoyo_overview,
        hoyo_realtime,
        language=lang,
        loader=loader,
    )
    card_data = await card_char.create(hide_credits=True)

    card_io = BytesIO(card_data)
    card_file = discord.File(card_io, f"{sel_uid}_ChroniclesOverview.QingqueBot.png")
    embed.set_image(url=f"attachment://{card_file.filename}")

    for idx, assignment in enumerate(hoyo_realtime.assignments, 1):
        assign_values = []
        assign_values.append(f"**{t('assignment.name')}**: {assignment.name}")
        assign_stat = f"**{t('assignment.status.title')}**: "
        if assignment.status.is_ongoing():
            assign_stat += t("assignment.status.ongoing")
        else:
            assign_stat += t("assignment.status.completed")
        assign_values.append(assign_stat)
        relative_done = int(round(hoyo_realtime.requested_at + assignment.time_left))
        assign_values.append(f"**{t('assignment.finish')}**: <t:{relative_done}:f>")
        embed.add_field(name=f"{t('assignment.title', [str(idx)])}", value="\n".join(assign_values), inline=True)

    logger.info("Sending to Discord...")
    await original_message.edit(content=None, embed=embed, attachments=[card_file])


@app_commands.command(name="srcharacters", description=locale_str("srcharacters.desc"))
async def qqprofile_srcharacters(inter: discord.Interaction[QingqueClient]):
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
            await original_message.edit(content=t("exception", [f"```{error_message}```"]))
            return

        if select_account.account is None:
            return await original_message.edit(content=t("srchoices.timeout"))

        sel_uid = select_account.account.uid
    else:
        sel_uid = profile.games[0].uid

    logger.info(f"Getting profile info for UID {sel_uid}")
    try:
        hoyo_user_info = await hoyoapi.get_battle_chronicles_basic_info(
            sel_uid,
            hylab_id=profile.hylab_id,
            hylab_token=profile.hylab_token,
            hylab_mid_token=profile.hylab_mid_token,
            lang=HYLanguage(lang.value.lower()),
        )
    except HYDataNotPublic:
        logger.warning(f"UID {sel_uid} data is not public.")
        await original_message.edit(content=t("hoyolab_public"))
        return
    except Exception as e:
        logger.error(f"Error getting profile info for UID {sel_uid}: {e}")
        error_message = str(e)
        await original_message.edit(content=t("exception", [f"```{error_message}```"]))
        return
    logger.info(f"Getting profile characters for UID {sel_uid}")
    try:
        hoyo_characters = await hoyoapi.get_battle_chronicles_characters(
            sel_uid,
            hylab_id=profile.hylab_id,
            hylab_token=profile.hylab_token,
            hylab_mid_token=profile.hylab_mid_token,
            lang=HYLanguage(lang.value.lower()),
        )
    except HYDataNotPublic:
        logger.warning(f"UID {sel_uid} data is not public.")
        await original_message.edit(content=t("hoyolab_public"))
        return
    except Exception as e:
        logger.error(f"Error getting profile characters for UID {sel_uid}: {e}")
        error_message = str(e)
        await original_message.edit(content=t("exception", [f"```{error_message}```"]))
        return

    if hoyo_user_info is None:
        logger.warning(f"UID {sel_uid} data is not available.")
        await original_message.edit(content=t("hoyolab_unavailable"))
        return

    if hoyo_characters is None:
        logger.warning(f"UID {sel_uid} data is not available. (Characters)")
        await original_message.edit(content=t("hoyolab_unavailable"))
        return

    logger.info(f"Generating profile characters card for {sel_uid}...")
    chara_gen = StarRailCharactersCard(
        hoyo_user_info, hoyo_characters, language=lang, loader=inter.client.get_srs(lang)
    )
    chara_bytes = await chara_gen.create(hide_credits=True)

    chara_io = BytesIO(chara_bytes)
    chara_io.seek(0)
    chara_file = discord.File(chara_io, filename=f"{sel_uid}_Characters.QingqueBot.png")

    await original_message.edit(attachments=[chara_file])


async def _make_rogue_card(
    inter: discord.Interaction[QingqueClient],
    rogue: ChronicleRoguePeriodRun | ChronicleRogueLocustDetailRecord,
    user: ChronicleRogueUserInfo,
    overview: ChronicleRogueOverview | ChronicleRogueLocustOverview,
    filename_pre: str,
    period_total: int | None = None,
    previous_period: bool = False,
) -> PagingChoice:
    lang = QingqueLanguage.from_discord(inter.locale)
    t = get_i18n_discord(inter.locale)
    rogue_title = t("chronicle_titles.rogue")
    if isinstance(rogue, ChronicleRogueLocustDetailRecord):
        rogue_title = t("chronicle_titles.rogue_locust")
    embed = discord.Embed(
        title=rogue_title,
        colour=_COMMON_FOREGROUND
        if isinstance(rogue, ChronicleRoguePeriodRun)
        else discord.Colour.from_rgb(189, 172, 255),
    )
    embed.set_author(name=user.name)
    descriptions = []
    if isinstance(rogue, ChronicleRoguePeriodRun):
        descriptions.append(
            t("chronicles.rogue.period_now") if not previous_period else t("chronicles.rogue.preiod_before")
        )

    if period_total is not None:
        descriptions.append(f"**{t('chronicles.rogue.num_clears')}**: {period_total:,}")
    if isinstance(overview, ChronicleRogueOverview):
        descriptions.append(f"**{t('chronicles.rogue.unlock_ability')}**: {overview.unlocked_skills:,}")
        descriptions.append(f"**{t('chronicles.rogue.unlock_curio')}**: {overview.unlocked_curios:,}")
        descriptions.append(f"**{t('chronicles.rogue.unlock_blessing')}**: {overview.unlocked_blessings:,}")
    else:
        stats = overview.stats
        descriptions.append(f"**{t('chronicles.rogue.locust_narrow')}**: {stats.pathstrider:,}")
        descriptions.append(f"**{t('chronicles.rogue.unlock_curio')}**: {stats.curios:,}")
        descriptions.append(f"**{t('chronicles.rogue.unlock_event')}**: {stats.events:,}")
    end_time = rogue.end_time.datetime
    challenged_on = f"<t:{int(end_time.timestamp())}:f>"
    challenged_tl = t("chronicles.challenged_on", ["REPLACEME"])
    # Find REPLACEME
    replace_me_idx = challenged_tl.find("REPLACEME")
    # Add bold to the challenged on text but not the timestamp
    challenged_tl = "**" + challenged_tl[:replace_me_idx].rstrip() + "**: " + challenged_tl[replace_me_idx:]
    challenged_tl = challenged_tl.replace("REPLACEME", challenged_on)
    descriptions.append(challenged_tl)

    gen_card = StarRailSimulatedUniverseCard(
        user,
        rogue,
        overview.destiny if isinstance(overview, ChronicleRogueLocustOverview) else [],
        language=lang,
        loader=inter.client.get_srs(lang),
    )

    end_time_fmt = end_time.strftime("%a, %b %d %Y %H:%M")

    card_bytes = await gen_card.create(hide_credits=True)
    card_fn = f"SimulatedUniverse_Run{filename_pre}.QingqueBot.png"
    card_io = FileBytes(card_bytes, filename=card_fn)
    title = t("chronicles.rogue.title")
    if isinstance(rogue, ChronicleRogueLocustDetailRecord):
        title += ": " + t("chronicles.rogue.title_locust")
    if isinstance(rogue, ChronicleRoguePeriodRun):
        title_world = "| " + t("rogue_world", [str(rogue.progress)])
        title_world += f" — {get_roman_numeral(rogue.difficulty, lang=lang)}"
    else:
        title_world = " — " + get_roman_numeral(rogue.difficulty, lang=lang)
    title += f" {title_world} | {end_time_fmt} UTC+8"
    emoji_icon = None
    if isinstance(rogue, ChronicleRoguePeriodRun):
        emoji_icon = inter.client.custom_emojis.get(f"su_world{rogue.progress}")
    else:
        emoji_icon = inter.client.custom_emojis.get("su_swarmdlc")
    embed.description = "\n".join(descriptions)
    embed.set_image(url=f"attachment://{card_fn}")
    return PagingChoice(
        title,
        embed,
        file=card_io,
        emoji=emoji_icon,
    )


@app_commands.command(name="srsimuniverse", description=locale_str("srsimuniverse.desc"))
async def qqprofile_srrogue(inter: discord.Interaction[QingqueClient]):
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
            await original_message.edit(content=t("exception", [f"```{error_message}```"]))
            return

        if select_account.account is None:
            return await original_message.edit(content=t("srchoices.timeout"))

        sel_uid = select_account.account.uid
    else:
        sel_uid = profile.games[0].uid

    logger.info(f"Getting profile simulated universe for UID {sel_uid}")
    try:
        hoyo_rogue = await hoyoapi.get_battle_chronicles_simulated_universe(
            sel_uid,
            hylab_id=profile.hylab_id,
            hylab_token=profile.hylab_token,
            hylab_mid_token=profile.hylab_mid_token,
            lang=HYLanguage(lang.value.lower()),
        )
    except HYDataNotPublic:
        logger.warning(f"UID {sel_uid} data is not public.")
        await original_message.edit(content=t("hoyolab_public"))
        return
    except Exception as e:
        logger.error(f"Error getting profile info for UID {sel_uid}: {e}")
        error_message = str(e)
        await original_message.edit(content=t("exception", [f"```{error_message}```"]))
        return
    logger.info(f"Getting profile simulated universe: swarm DLC for UID {sel_uid}")
    try:
        hoyo_locust = await hoyoapi.get_battle_chronicles_simulated_universe_swarm_dlc(
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
        await original_message.edit(content=t("exception", [f"```{error_message}```"]))
        return

    if hoyo_rogue is None:
        logger.warning(f"UID {sel_uid} data is not available. (Rogue)")
        await original_message.edit(content=t("hoyolab_unavailable"))
        return

    if hoyo_locust is None:
        logger.warning(f"UID {sel_uid} data is not available. (Locust)")
        await original_message.edit(content=t("hoyolab_unavailable"))
        return

    async def _run_rogue_wrapper(
        sorting: str,
        simu: ChronicleRogueLocustDetailRecord | ChronicleRoguePeriodRun,
        overview: ChronicleRogueOverview | ChronicleRogueLocustOverview,
        user: ChronicleRogueUserInfo,
        filename_pre: str,
        total_run: int | None = None,
        previous_run: bool = False,
    ):
        logger.info(f"Generating simulated universe card for {user.name} | {type(simu)} | {sorting}...")
        data = await _make_rogue_card(
            inter,
            simu,
            user,
            overview,
            filename_pre,
            period_total=total_run,
            previous_period=previous_run,
        )
        return data, sorting

    rogue_over = hoyo_rogue.overview
    task_managerials: list[Coroutine[Any, Any, tuple[PagingChoice, str]]] = []
    for idx, simu in enumerate(hoyo_rogue.current.records):
        task_managerials.append(
            _run_rogue_wrapper(
                f"01_{idx:03d}",
                simu,
                rogue_over,
                hoyo_rogue.user,
                f"Current{idx:02d}",
                total_run=hoyo_rogue.current.overview.total_run,
            )
        )
    for idx, simu in enumerate(hoyo_rogue.previous.records):
        task_managerials.append(
            _run_rogue_wrapper(
                f"02_{idx:03d}",
                simu,
                rogue_over,
                hoyo_rogue.user,
                f"Previous{idx:02d}",
                total_run=hoyo_rogue.current.overview.total_run,
                previous_run=True,
            )
        )
    for idx, simu in enumerate(hoyo_locust.details.records):
        task_managerials.append(
            _run_rogue_wrapper(
                f"03_{idx:03d}",
                simu,
                hoyo_locust.overview,
                hoyo_locust.user,
                f"Locust{idx:02d}",
            )
        )

    task_executor: list[tuple[PagingChoice, str]] = await asyncio.gather(*task_managerials)
    task_executor.sort(key=lambda x: x[1])
    paging_choices: list[PagingChoice] = [x[0] for x in task_executor]

    logger.info("Sending to Discord...")
    pagination_view = EmbedPagingSelectView(paging_choices, inter.locale, user_id=inter.user.id)
    await pagination_view.start(original_message)


async def _make_moc_card(
    inter: discord.Interaction[QingqueClient],
    floor: ChronicleFHFloor,
    overall: ChronicleForgottenHall,
    sorter: str,
    previous_period: bool = False,
) -> PagingChoice:
    lang = QingqueLanguage.from_discord(inter.locale)
    t = get_i18n_discord(inter.locale)
    embed = discord.Embed(title=t("chronicle_titles.abyss"), colour=discord.Colour.from_rgb(178, 57, 80))
    descriptions = []

    start_time = int(overall.start_time.datetime.astimezone(timezone.utc).timestamp())
    end_time = int(overall.end_time.datetime.astimezone(timezone.utc).timestamp())
    period_desc = t("chronicles.moc_periods", [f"<t:{start_time}:f>", f"<t:{end_time}:f>"])
    period_timing = t("chronicles.rogue.period_now") if not previous_period else t("chronicles.rogue.preiod_before")
    period_desc = f"{period_desc} ({period_timing})"

    descriptions.append(period_desc)
    descriptions.append(f"**{t('chronicles.moc_stars')}**: {overall.total_stars:,}")
    descriptions.append(f"**{t('chronicles.moc_battles')}**: {overall.total_battles:,}")
    challenge_time = floor.node_1.challenge_time.datetime.astimezone(timezone.utc)
    challenged_on = f"<t:{int(challenge_time.timestamp())}:f>"
    challenged_tl = t("chronicles.challenged_on", ["REPLACEME"])
    # Find REPLACEME
    replace_me_idx = challenged_tl.find("REPLACEME")
    # Add bold to the challenged on text but not the timestamp
    challenged_tl = "**" + challenged_tl[:replace_me_idx].strip() + "**: " + challenged_tl[replace_me_idx:]
    challenged_tl = challenged_tl.replace("REPLACEME", challenged_on)
    descriptions.append(challenged_tl)

    gen_card = StarRailMoCCard(
        floor,
        language=lang,
        loader=inter.client.get_srs(lang),
    )

    challenge_time_fmt = challenge_time.strftime("%a, %b %d %Y %H:%M")

    card_bytes = await gen_card.create(hide_credits=True)
    card_fn = f"MemoryOfChaos_{sorter}.QingqueBot.png"
    card_io = FileBytes(card_bytes, filename=card_fn)
    title = strip_unity_rich_text(floor.name) + " | " + challenge_time_fmt
    embed.description = "\n".join(descriptions)
    embed.set_image(url=f"attachment://{card_fn}")
    return PagingChoice(
        title,
        embed,
        file=card_io,
    )


@app_commands.command(name="srmoc", description=locale_str("srmoc.desc"))
@app_commands.describe(previous=locale_str("srmoc.previous_desc"))
async def qqprofile_moc(inter: discord.Interaction[QingqueClient], previous: bool = False):
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
            await original_message.edit(content=t("exception", [f"```{error_message}```"]))
            return

        if select_account.account is None:
            return await original_message.edit(content=t("srchoices.timeout"))

        sel_uid = select_account.account.uid
    else:
        sel_uid = profile.games[0].uid

    logger.info(f"Getting profile memory of chaos for UID {sel_uid}")
    try:
        hoyo_moc = await hoyoapi.get_battle_chronicles_forgotten_hall(
            sel_uid,
            previous=previous,
            hylab_id=profile.hylab_id,
            hylab_token=profile.hylab_token,
            hylab_mid_token=profile.hylab_mid_token,
            lang=HYLanguage(lang.value.lower()),
        )
    except HYDataNotPublic:
        logger.warning(f"UID {sel_uid} data is not public.")
        await original_message.edit(content=t("hoyolab_public"))
        return
    except Exception as e:
        logger.error(f"Error getting profile info for UID {sel_uid}: {e}")
        error_message = str(e)
        await original_message.edit(content=t("exception", [f"```{error_message}```"]))
        return

    if hoyo_moc is None:
        logger.warning(f"UID {sel_uid} data is not available. (MoC)")
        await original_message.edit(content=t("hoyolab_unavailable"))
        return

    if not hoyo_moc.has_data:
        logger.warning(f"UID {sel_uid} has no data for this period. (MoC)")
        await original_message.edit(content=t("srmoc.no_data"))
        return

    async def _run_moc_wrapper(
        sorting: str,
        floor: ChronicleFHFloor,
        overall: ChronicleForgottenHall,
    ):
        logger.info(f"Generating moc card for {sel_uid} | {sorting}...")
        data = await _make_moc_card(
            inter,
            floor,
            overall,
            sorting,
            previous_period=previous,
        )
        return data, sorting

    task_managerials: list[Coroutine[Any, Any, tuple[PagingChoice, str]]] = []
    for idx, floor in enumerate(hoyo_moc.floors):
        task_managerials.append(
            _run_moc_wrapper(
                f"01_{idx:03d}",
                floor,
                hoyo_moc,
            )
        )

    task_executor: list[tuple[PagingChoice, str]] = await asyncio.gather(*task_managerials)
    task_executor.sort(key=lambda x: x[1])
    paging_choices: list[PagingChoice] = [x[0] for x in task_executor]

    logger.info("Sending to Discord...")
    pagination_view = EmbedPagingSelectView(paging_choices, inter.locale, user_id=inter.user.id)
    await pagination_view.start(original_message)
