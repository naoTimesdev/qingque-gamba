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

import logging
from typing import ClassVar

from qingque.hylab.models.base import HYLanguage
from qingque.hylab.models.simuniverse import (
    ChronicleRogueBlessingItem,
    ChronicleRogueLocustDetailRecord,
    ChronicleRoguePeriodRun,
    ChronicleRogueUserInfo,
)
from qingque.i18n import QingqueLanguage, get_roman_numeral
from qingque.mihomo.models.constants import MihomoLanguage
from qingque.utils import strip_unity_rich_text

from .base import RGB, StarRailDrawing

__all__ = ("StarRailSimulatedUniverseCard",)
logger = logging.getLogger("qingque.starrail.generator.simuniverse")


def _text_fixup(text: str):
    text = strip_unity_rich_text(text)
    text = text.replace("≪", "<<")
    text = text.replace("≫", ">>")
    return text


class StarRailSimulatedUniverseCard(StarRailDrawing):
    MARGIN_LR = 75
    MARGIN_TP = 75
    FIVE_GRADIENT: ClassVar[tuple[RGB, RGB]] = ((117, 70, 66), (201, 164, 104))
    FOUR_GRADIENT: ClassVar[tuple[RGB, RGB]] = ((55, 53, 87), (134, 89, 204))

    RARITY_COLOR: ClassVar[dict[int, RGB]] = {
        1: (83, 85, 95),
        2: (52, 75, 123),
        3: (152, 108, 82),
    }
    RARITY_GRADIANT: ClassVar[dict[int, tuple[RGB, RGB]]] = {
        1: ((49, 51, 64), (130, 131, 138)),
        2: ((45, 47, 81), (68, 116, 187)),
        3: FIVE_GRADIENT,
    }

    def __init__(
        self,
        user: ChronicleRogueUserInfo,
        record: ChronicleRoguePeriodRun | ChronicleRogueLocustDetailRecord,
        *,
        language: MihomoLanguage | HYLanguage | QingqueLanguage = MihomoLanguage.EN,
    ) -> None:
        super().__init__(language=language)
        self._record = record
        self._user = user

        self._background = (18, 18, 18)
        self._foreground = (219, 194, 145)
        self._make_canvas(width=2000, height=1125, color=self._background)

    async def _create_world_header(self) -> None:
        icon_url = self._record.icon_url
        icon_image = await self._async_open(self._assets_folder / icon_url)
        icon_image = await self._resize_image(icon_image, (200, 200))
        await self._paste_image(icon_image, (self.MARGIN_LR, self.MARGIN_TP), icon_image)
        rogue_title = self._i18n.t("chronicles.rogue.title")
        rogue_diff = get_roman_numeral(self._record.difficulty, lang=self._language)
        if isinstance(self._record, ChronicleRogueLocustDetailRecord):
            # Make use of normal translation.
            rogue_sub_title = self._i18n.t("chronicles.rogue.title_locust")
        else:
            rogue_sub_title = self._i18n.t("rogue_world", [str(self._record.progress)])
            rogue_sub_title += f" — {rogue_diff}"
        await self._write_text(
            rogue_title,
            (self.MARGIN_LR + 235, self.MARGIN_TP + (icon_image.height // 2) - 20),
            font_size=70,
            anchor="ls",
        )
        await self._write_text(
            rogue_sub_title,
            (self.MARGIN_LR + 235, self.MARGIN_TP + (icon_image.height // 2) + 60),
            font_size=50,
            anchor="ls",
        )
        await self._async_close(icon_image)

        # Top-right for score
        if isinstance(self._record, ChronicleRoguePeriodRun):
            rogue_score = self._i18n.t("chronicles.rogue.score_high")
            await self._write_text(
                rogue_score,
                (self._canvas.width - self.MARGIN_LR, self.MARGIN_TP + (icon_image.height // 2) - 20),
                font_size=70,
                anchor="rs",
                align="right",
            )
            await self._write_text(
                f"{self._record.score:,}",
                (self._canvas.width - self.MARGIN_LR, self.MARGIN_TP + (icon_image.height // 2) + 60),
                font_size=50,
                anchor="rs",
                align="right",
            )
        else:
            await self._write_text(
                rogue_diff,
                (self._canvas.width - self.MARGIN_LR, self.MARGIN_TP + (icon_image.height // 2) + 30),
                font_size=100,
                anchor="rs",
                align="right",
            )

    async def _create_character_profile(self):
        MARGIN_TOP = self.MARGIN_TP + 240

        inbetween_margin = 190
        for idx, lineup in enumerate(self._record.final_lineups, 0):
            chara_icon = await self._async_open(self._assets_folder / lineup.icon_path)
            chara_icon = await self._resize_image(chara_icon, (150, 150))
            # Create backdrop
            gradient = self.FIVE_GRADIENT if lineup.rarity == 5 else self.FOUR_GRADIENT
            await self._create_box_2_gradient(
                (
                    self.MARGIN_LR + (inbetween_margin * idx),
                    MARGIN_TOP,
                    self.MARGIN_LR + (inbetween_margin * idx) + chara_icon.width,
                    MARGIN_TOP + chara_icon.height,
                ),
                gradient,
            )
            # Add the character icon
            await self._paste_image(
                chara_icon,
                (self.MARGIN_LR + (inbetween_margin * idx), MARGIN_TOP),
                chara_icon,
            )
            # Create the backdrop for the level
            await self._create_box(
                (
                    (self.MARGIN_LR + (inbetween_margin * idx), MARGIN_TOP + chara_icon.height),
                    (
                        self.MARGIN_LR + (inbetween_margin * idx) + chara_icon.height,
                        MARGIN_TOP + chara_icon.height + 30,
                    ),
                )
            )
            # Write the level
            await self._write_text(
                self._i18n.t("chronicles.level_short", [f"{lineup.level:02d}"]),
                (
                    self.MARGIN_LR + (inbetween_margin * idx) + (chara_icon.width // 2),
                    MARGIN_TOP + chara_icon.height + 22,
                ),
                font_size=20,
                anchor="ms",
                color=self._background,
            )

            # Create backdrop for eidolons (top right)
            await self._create_box(
                (
                    (self.MARGIN_LR + (inbetween_margin * idx) + chara_icon.width - 30, MARGIN_TOP),
                    (self.MARGIN_LR + (inbetween_margin * idx) + chara_icon.width, MARGIN_TOP + 30),
                )
            )
            # Write the eidolon
            await self._write_text(
                f"E{lineup.eidolons}",
                (self.MARGIN_LR + (inbetween_margin * idx) + chara_icon.width - 15, MARGIN_TOP + 22),
                font_size=20,
                anchor="ms",
                color=self._background,
            )
            await self._async_close(chara_icon)

    async def _create_obtained_blessings(self) -> float:
        MARGIN_TOP = self.MARGIN_TP + 450
        ICON_SIZE = 50
        MAX_WIDTH = self._canvas.width - self.MARGIN_LR - (ICON_SIZE * 2) - 60
        TEXT_SIZE = 20
        TEXT_MARGIN = 13

        # How this works?
        # We start from the afformentioned margin top, and we will go to the maximum of 1774 in length total
        # If it exceeds, we will go to the next line.
        # Extend the line by 50 pixels.

        for blessing_info in self._record.blessings:
            kind_info = blessing_info.kind
            blessings = blessing_info.items

            bless_info = self._index_data.simuniverse_blessing_types[str(kind_info.id)]
            # Create the blessings parting
            bless_icon = await self._async_open(self._assets_folder / bless_info.icon_url)
            # Resize
            bless_icon = await self._resize_image(bless_icon, (ICON_SIZE, ICON_SIZE))
            await self._paste_image(
                bless_icon,
                (self.MARGIN_LR, MARGIN_TOP),
                bless_icon,
            )
            await self._async_close(bless_icon)
            # Write path name
            await self._write_text(
                bless_info.name,
                (self.MARGIN_LR + 60, MARGIN_TOP + 18),
                font_size=18,
                anchor="ls",
            )

            # Start writing the blessings
            # We will create it into a nested blessings first before writing it.
            _temp_nested_blessings = []
            _temp_current_length = 0
            nested_blessings: list[list[ChronicleRogueBlessingItem]] = []
            for blessing in blessings:
                bless_item = self._index_data.simuniverse_blessings[str(blessing.id)]
                calc_length = await self._calc_text(_text_fixup(bless_item.name), font_size=TEXT_SIZE)
                _temp_current_length += calc_length + TEXT_MARGIN
                if _temp_current_length >= MAX_WIDTH:
                    nested_blessings.append(_temp_nested_blessings)
                    _temp_nested_blessings = []
                    _temp_current_length = calc_length + TEXT_MARGIN
                _temp_nested_blessings.append(blessing)
            if _temp_nested_blessings:
                nested_blessings.append(_temp_nested_blessings)

            total_xtend_down = 0
            for _ in nested_blessings:
                total_xtend_down += 30
            total_xtend_down += 65

            # Margin bottom + 65
            canvas_max = self._canvas.height - self.MARGIN_TP
            bottom_part = MARGIN_TOP + total_xtend_down
            if bottom_part >= canvas_max:
                # We need to extend the canvas.
                extended = bottom_part - canvas_max
                if extended < 0:
                    extended = canvas_max - bottom_part
                await self._extend_canvas_down(extended)

            for bless_nest in nested_blessings:
                start_left = self.MARGIN_LR + 60
                for blessing in bless_nest:
                    bless_item = self._index_data.simuniverse_blessings[str(blessing.id)]
                    # Create the box
                    calc_length = await self._calc_text(_text_fixup(bless_item.name), font_size=TEXT_SIZE)
                    if blessing.enhanced:
                        rarity_grad = self.RARITY_GRADIANT[blessing.rank]
                        await self._create_box_2_gradient(
                            (int(start_left), MARGIN_TOP + 28, int(start_left + calc_length + 6), MARGIN_TOP + 52),
                            rarity_grad,
                            movement="hor",
                        )
                    else:
                        rarity_col = self.RARITY_COLOR[blessing.rank]
                        await self._create_box(
                            (
                                (start_left, MARGIN_TOP + 28),
                                (
                                    start_left + calc_length + 6,
                                    MARGIN_TOP + 52,
                                ),
                            ),
                            color=rarity_col,
                        )
                    await self._write_text(
                        _text_fixup(bless_item.name),
                        (start_left + 3, MARGIN_TOP + 46),
                        font_size=TEXT_SIZE,
                        anchor="ls",
                        color=(255, 255, 255),
                    )
                    start_left += calc_length + TEXT_MARGIN
                MARGIN_TOP += 30
            MARGIN_TOP -= 30
            MARGIN_TOP += 65

        return MARGIN_TOP

    async def _create_obtained_curios(self, margin_top: float):
        pass

    async def create(self, *, hide_credits: bool = False):
        self._assets_folder = await self._assets_folder.absolute()
        if not await self._assets_folder.exists():
            raise FileNotFoundError("The assets folder does not exist.")
        await self._index_data.async_loads()

        # Write the username
        logger.info("Writing world header...")
        await self._create_world_header()

        logger.info("Writing character profile...")
        await self._create_character_profile()

        logger.info("Writing obtained blessings...")
        obtain_max = await self._create_obtained_blessings()

        logger.info("Writing obtained curios...")
        await self._create_obtained_curios(obtain_max)

        # Create footer
        logger.info("Creating footer...")
        await self._write_text(
            "Supported by Interastral Peace Corporation",
            (20, self._canvas.height - 20),
            font_size=20,
            alpha=128,
            font_path=self._universe_font_path,
            anchor="ls",
        )
        if not hide_credits:
            await self._write_text(
                self._i18n.t("chronicles.credits"),
                (self._canvas.width - 20, self._canvas.height - 20),
                font_size=20,
                alpha=128,
                anchor="rs",
            )

        # Save the image.
        logger.info("Saving the image...")
        bytes_io = await self._async_save_bytes(self._canvas)

        logger.info("Cleaning up...")
        await self._async_close(self._canvas)

        # Return the bytes.
        bytes_io.seek(0)
        all_bytes = await self._loop.run_in_executor(None, bytes_io.read)
        bytes_io.close()
        self._index_data.unloads()
        return all_bytes
