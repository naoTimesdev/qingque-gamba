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

import importlib
from pathlib import Path
from typing import Any

import discord
from aiopath import AsyncPath
from discord import app_commands
from discord.flags import Intents

from qingque.mihomo.client import MihomoAPI
from qingque.models.config import QingqueConfig
from qingque.redisdb import RedisDatabase
from qingque.tooling import get_logger

__all__ = ("QingqueClient",)
ROOT_DIR = Path(__file__).parent.absolute().parent


class QingqueClient(discord.Client):
    def __init__(self, config: QingqueConfig, *, intents: Intents, **options: Any) -> None:
        super().__init__(intents=intents, **options)

        self.logger = get_logger("qingque.client")
        self.tree = app_commands.CommandTree(self)

        self._config: QingqueConfig = config
        self._mihomo: MihomoAPI | None = None
        self._redis: RedisDatabase | None = None

    @property
    def mihomo(self) -> MihomoAPI:
        if self._mihomo is None:
            raise RuntimeError("Mihomo client is not setup yet.")
        return self._mihomo

    @property
    def config(self) -> QingqueConfig:
        return self._config

    @property
    def redis(self) -> RedisDatabase:
        if self._redis is None:
            raise RuntimeError("Redis client is not setup yet.")
        return self._redis

    async def setup_hook(self) -> None:
        self.logger.info("Setting up the bot...")

        self.logger.info("Setting up Redis client...")
        redisdb = RedisDatabase(
            host=self._config.redis.host,
            port=self._config.redis.port,
            password=self._config.redis.password,
        )
        await redisdb.connect()
        self.logger.info("Redis client connected.")
        self._redis = redisdb

        self.logger.info("Setting up Mihomo client...")
        self._mihomo = MihomoAPI()
        self.logger.info("Loading extensions...")
        await self.load_extensions()
        self.logger.info("Syncing commands...")
        await self.tree.sync()
        self.logger.info("Bot is ready.")

    async def available_extensions(self):
        COGS_FOLDER = AsyncPath(ROOT_DIR / "cogs")
        IGNORED_FILES = ["__init__", "__main__"]

        # See cogs folder
        commands: list[app_commands.Command] = []
        async for cogs_file in COGS_FOLDER.rglob("*.py"):
            if cogs_file.stem.lower() in IGNORED_FILES:
                continue

            # Get the cog path
            # ex: cogs/xxxx/a.py
            #     cogs/b.py

            cog_parts = list(cogs_file.relative_to(COGS_FOLDER.parent).parts)
            # Remove .py from the last part
            cog_parts[-1] = Path(cog_parts[-1]).stem
            cog_path = ".".join(cog_parts)

            module = importlib.import_module(cog_path)
            # Get all functions in the module
            # and check if it's a Command.
            for obj in module.__dict__.values():
                if isinstance(obj, app_commands.Command):
                    commands.append(obj)
        return commands

    async def load_extensions(self) -> None:
        all_extensions = await self.available_extensions()
        for extension in all_extensions:
            self.logger.info(f"Loading extension {extension}")
            try:
                self.tree.add_command(extension)
            except Exception as e:
                self.logger.error(f"Failed to load extension {extension}", exc_info=e)

    async def close(self) -> None:
        self.logger.info("Closing the bot...")

        if self._mihomo is not None:
            self.logger.info("Closing Mihomo client...")
            await self._mihomo.close()
            self.logger.info("Mihomo client closed.")

        if self._redis is not None:
            self.logger.info("Closing Redis client...")
            await self._redis.close()
            self.logger.info("Redis client closed.")

        return await super().close()
