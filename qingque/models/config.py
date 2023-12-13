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

from pathlib import Path

import msgspec
from aiopath import AsyncPath
from msgspec import Struct

__all__ = (
    "QingqueConfig",
    "QingqueConfigHoyolab",
    "QingqueConfigRedis",
    "load_config",
    "save_config",
    "reload_config",
)


class QingqueConfigHoyolab(Struct):
    ltuid: int
    """:class:`int`: The ltuid."""
    ltoken: str
    """:class:`str`: The ltoken."""


class QingqueConfigRedis(Struct):
    host: str
    """:class:`str`: The Redis host."""
    port: int
    """:class:`int`: The Redis port."""
    password: str | None = None
    """:class:`str | None`: The Redis password."""


class QingqueConfig(Struct):
    bot_id: int
    """:class:`int`: The bot ID."""
    bot_token: str
    """:class:`str`: The bot token."""
    api_endpoint: str
    """:class:`str`: The API endpoint of Qingque API."""

    redis: QingqueConfigRedis
    """:class:`QingqueConfigRedis`: The Redis config."""

    hoyolab: QingqueConfigHoyolab | None = None
    """:class:`QingqueConfigHoyolab | None`: The HoyoLab config."""
    api_token: str | None = None
    """:class:`str | None`: The strict API token of Qingque API."""


def load_config() -> QingqueConfig:
    root_dir = Path(__file__).absolute().parent.parent.parent

    config_toml = root_dir / "config.toml"
    if not config_toml.exists():
        raise RuntimeError("Config file is not found.")

    return msgspec.toml.decode(config_toml.read_bytes(), type=QingqueConfig)


async def save_config(config: QingqueConfig) -> None:
    root_dir = (await AsyncPath(__file__).absolute()).parent.parent.parent

    config_toml = root_dir / "config.toml"
    await config_toml.write_bytes(msgspec.toml.encode(config))


async def reload_config():
    root_dir = (await AsyncPath(__file__).absolute()).parent.parent.parent

    config_toml = root_dir / "config.toml"
    return msgspec.toml.decode(await config_toml.read_bytes(), type=QingqueConfig)
