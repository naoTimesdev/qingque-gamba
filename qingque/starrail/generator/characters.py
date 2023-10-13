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

from typing import TYPE_CHECKING

from qingque.hylab.models.characters import ChronicleCharacters
from qingque.hylab.models.overview import ChronicleUserInfo
from qingque.mihomo.models.constants import MihomoLanguage
from qingque.starrail.caching import StarRailImageCache
from qingque.tooling import get_logger

from .base import StarRailDrawing, StarRailDrawingLogger
from .mixins import SRDrawCharacter, StarRailDrawCharacterMixin, StarRailDrawDecoMixin

if TYPE_CHECKING:
    from qingque.hylab.models.base import HYLanguage
    from qingque.i18n import QingqueLanguage
    from qingque.starrail.loader import SRSDataLoader

__all__ = ("StarRailCharactersCard",)


class StarRailCharactersCard(StarRailDrawDecoMixin, StarRailDrawCharacterMixin, StarRailDrawing):
    MARGIN_LR = 75
    MARGIN_TP = 75

    MAX_PER_ROW = 10
    CHARACTER_SIZE = 150
    MARGIN_CHAR = 180
    MARGIN_CHAR_TOP = 50

    def __init__(
        self,
        user_info: ChronicleUserInfo,
        characters: ChronicleCharacters,
        *,
        language: MihomoLanguage | HYLanguage | QingqueLanguage = MihomoLanguage.EN,
        loader: SRSDataLoader | None = None,
        img_cache: StarRailImageCache | None = None,
    ) -> None:
        super().__init__(language=language, loader=loader, img_cache=img_cache)
        self._characters: ChronicleCharacters = characters

        self._user_info: ChronicleUserInfo = user_info
        self.logger = get_logger(
            "qingque.starrail.generator.characters",
            adapter=StarRailDrawingLogger.create(self._user_info.name),
        )

        self._background = (18, 18, 18)
        self._foreground = (219, 194, 145)
        self._make_canvas(width=1920, height=1080, color=self._background)

    async def _precalculate_characters(self):
        MARGIN_TOP = self.MARGIN_TP + 200
        # With level box
        ONE_HEIGHT = self.CHARACTER_SIZE + 30

        CANVAS_MAX = self._canvas.height - (self.MARGIN_TP * 2)

        # Total characters, split by 10
        chars = self._characters.characters
        total_characters = [chars[i : i + self.MAX_PER_ROW] for i in range(0, len(chars), self.MAX_PER_ROW)]

        # Total height needed
        total_height = MARGIN_TOP + (len(total_characters) * (ONE_HEIGHT + self.MARGIN_CHAR_TOP))
        if total_height > CANVAS_MAX:
            extend_by = total_height - CANVAS_MAX
            await self._extend_canvas_down(extend_by)

    async def _create_characters_rows(self):
        MARGIN_TOP = self.MARGIN_TP + 200

        await self._write_text(
            self._i18n.t("chronicles.characters"),
            (self.MARGIN_LR, MARGIN_TOP - 30),
            font_size=36,
            anchor="ls",
            align="left",
        )

        charas = self._characters.characters
        split_charas = [charas[i : i + self.MAX_PER_ROW] for i in range(0, len(charas), self.MAX_PER_ROW)]
        self.logger.info(f"Splitting characters into {len(split_charas)} rows.")

        for row_chars in split_charas:
            chars_coerce = [SRDrawCharacter.from_hylab(r) for r in row_chars]
            await self._create_character_card(
                chars_coerce,
                drawing=self,
                margin_lr=self.MARGIN_LR,
                margin_top=MARGIN_TOP,
                inbetween_margin=self.MARGIN_CHAR,
                icon_size=self.CHARACTER_SIZE,
            )
            MARGIN_TOP += self.CHARACTER_SIZE + 30 + self.MARGIN_CHAR_TOP

    async def create(self, *, hide_credits: bool = False, clear_cache: bool = True) -> bytes:
        self._assets_folder = await self._assets_folder.absolute()
        if not await self._assets_folder.exists():
            raise FileNotFoundError("The assets folder does not exist.")
        await self._index_data.async_loads()

        # Precalculate the characters
        await self._precalculate_characters()

        # Create the decoration.
        self.logger.info("Creating decoration...")
        await self._create_decoration(hide_credits, drawing=self)

        # Write the username and level
        self.logger.info("Writing username...")
        level_txt = self._i18n.t("chronicles.level_short", [f"{self._user_info.level:02d}"])
        length_max = await self._write_text(
            content=self._user_info.name,
            box=(self.MARGIN_LR, self.MARGIN_TP + 68),
            font_size=86,
            anchor="ls",
        )
        await self._write_text(
            content=f"({level_txt})",
            box=(self.MARGIN_LR + length_max + 20, self.MARGIN_TP + 68),
            font_size=54,
            anchor="ls",
        )

        self.logger.info("Writing characters row...")
        await self._create_characters_rows()

        # Create footer
        self.logger.info("Creating footer...")
        await self._write_text(
            "Supported by Interastral Peace Corporation",
            (20, self._canvas.height - 20),
            font_size=20,
            alpha=128,
            font_path=self._universe_font_path,
            anchor="ls",
        )

        # Create the credits
        if not hide_credits:
            await self._write_text(
                self._i18n.t("chronicles.credits") or "Data from HoyoLab | Created by @noaione",
                (self._canvas.width // 2, self._canvas.height - 20),
                font_size=16,
                alpha=128,
                anchor="ms",
            )

        # Save the image.
        self.logger.info("Saving the image...")
        bytes_io = await self._async_save_bytes(self._canvas)

        self.logger.info("Cleaning up...")
        await self.close(clear_cache)

        # Return the bytes.
        bytes_io.seek(0)
        all_bytes = await self._loop.run_in_executor(self.executor, bytes_io.read)
        bytes_io.close()
        self.shutdown_thread()
        return all_bytes
