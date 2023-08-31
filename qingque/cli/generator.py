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

import argparse
import asyncio
from pathlib import Path
from typing import cast

from qingque.mihomo import MihomoAPI
from qingque.starrail import StarRailCard
from qingque.tooling import setup_logger


class Argument(argparse.Namespace):
    uid: int
    hide_uid: bool
    hide_credits: bool
    index: int


async def runner(args: Argument):
    log = setup_logger()
    client = MihomoAPI()
    log.info(f"Fetching player data for {args.uid}")
    player, lang = await client.get_player(args.uid)
    await client.close()

    if not player.characters:
        log.error("No characters found")
        return None, None

    try:
        character = player.characters[args.index]
    except IndexError:
        log.warning(f"Character index {args.index} not found, falling back to 0")
        character = player.characters[0]

    log.info(f"Creating card for {character.name} ({character.id})")
    card = StarRailCard(character, player.player, language=lang)
    return await card.create(hide_uid=args.hide_uid, hide_credits=args.hide_credits), character


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("uid", type=int, help="UID of the player")
    parser.add_argument("--hide-uid", action="store_true", help="Hide the UID on the card")
    parser.add_argument("--hide-credits", action="store_true", help="Hide the credits on the card")
    parser.add_argument("-i", "--index", type=int, default=0, help="Zero-based index of the character to use")

    args = parser.parse_args()

    bytes_data, character = asyncio.run(runner(cast(Argument, args)))
    if bytes_data is not None and character is not None:
        target = Path.cwd() / f"{args.uid}_{character.id}_Card.png"
        target.write_bytes(bytes_data)
