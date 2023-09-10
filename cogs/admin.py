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

from qingque.bot import QingqueClient
from qingque.i18n import load_i18n_languages
from qingque.tooling import get_logger

__all__ = ("qqadmin_reload",)
OWNER_IDS = [466469077444067372]
logger = get_logger("cogs.admin")


def is_owner(inter: discord.Interaction[QingqueClient]):
    return inter.user.id in OWNER_IDS


@app_commands.command(name="srreload", description="Reload all translation files")
@app_commands.guilds(761916689113284638, 899109600509448232)
@app_commands.check(is_owner)
async def qqadmin_reload(inter: discord.Interaction[QingqueClient]):
    await inter.response.defer()

    logger.info("Reloading translation files...")
    await inter.client.loop.run_in_executor(None, load_i18n_languages)

    logger.info("Reloading SRS data...")
    await inter.client.load_srs_data()

    logger.info("Syncing commands again...")
    await inter.client.tree.sync()

    logger.info("Done!")
    await inter.edit_original_response(content="Reloaded everything!")
