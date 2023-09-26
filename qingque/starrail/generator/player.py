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
from typing import Any

from PIL import Image, ImageFilter

from qingque.hylab.models.base import HYLanguage
from qingque.i18n import QingqueLanguage
from qingque.mihomo.models.characters import Character
from qingque.mihomo.models.constants import MihomoLanguage
from qingque.mihomo.models.player import Player
from qingque.starrail.imaging import AsyncImageFilter
from qingque.starrail.loader import SRSDataLoader
from qingque.tooling import get_logger

from .base import StarRailDrawing, StarRailDrawingLogger

__all__ = ("StarRailPlayerCard",)


class StarRailPlayerCard(StarRailDrawing):
    MARGIN = 30

    def __init__(
        self,
        player: Player,
        *,
        language: MihomoLanguage | HYLanguage | QingqueLanguage = MihomoLanguage.EN,
        loader: SRSDataLoader | None = None,
    ) -> None:
        super().__init__(language=language, loader=loader)
        self.logger = get_logger(
            "qingque.starrail.generator.player", adapter=StarRailDrawingLogger.create(f"UID-{player.player.id}")
        )
        self._player = player.player
        self._characters = player.characters
        self._images_dir = self._assets_folder / ".." / "images"

    async def _init_canvas(self) -> None:
        mask_data = await self._async_open(self._images_dir / "MihomoCardMask.png")
        star_rail = await self._async_open(self._images_dir / "StarrailStartBG.jpg")
        star_rail = await self._resize_image_side(
            star_rail, target=3000, side="width", resampling=Image.Resampling.BICUBIC
        )

        # Create a masked image
        canvas = Image.new("RGBA", (mask_data.width, mask_data.height), (0, 0, 0, 0))
        # Crop star rail, make it to the middle crop.
        START_TOP = 300
        START_END = START_TOP + canvas.height
        MID_CANVAS = canvas.width // 2
        MID_STAR_RAIL = star_rail.width // 2
        star_rail = await self._crop_image(
            star_rail,
            (MID_STAR_RAIL - MID_CANVAS, START_TOP, MID_STAR_RAIL + MID_CANVAS, START_END),
        )
        # Blur the image
        star_rail = await AsyncImageFilter.process(star_rail, subclass=ImageFilter.GaussianBlur(5))
        await self._paste_image(
            star_rail,
            (0, 0),
            mask_data,
            canvas=canvas,
        )
        self._canvas = canvas
        frost_mask = await self._async_open(self._images_dir / "MihomoCardFrostMask.png")

        if len(self._characters) > 0:
            self.logger.info("Creating the main support character.")
            main_char = self._characters[0]
            chara_mask = await self._async_open(self._images_dir / "MihomoCardCharMask.png")
            chara_potrait = await self._async_open(self._assets_folder / main_char.portrait_url)
            chara_potrait = await self._resize_image_side(
                chara_potrait, target=self._canvas.height, side="h", resampling=Image.Resampling.BICUBIC
            )
            chara_canvas = Image.new("RGBA", (chara_mask.width, chara_mask.height), (0, 0, 0, 0))
            await self._paste_image(
                star_rail,
                (0, 0),
                star_rail,
                canvas=chara_canvas,
            )
            await self._paste_image(chara_potrait, (-200, 0), chara_potrait, canvas=chara_canvas)
            chara_mask = await self._set_transparency(chara_mask, 0)
            await self._paste_image(chara_canvas, (0, 0), chara_mask)

            # Paste the character canvas to the main canvas.
            chara_blurred = await AsyncImageFilter.process(chara_canvas, subclass=ImageFilter.GaussianBlur(20))
            await self._paste_image(chara_blurred, (0, 0), frost_mask)
            await self._async_close(chara_blurred)
            await self._async_close(chara_canvas)
            await self._async_close(chara_potrait)
            await self._async_close(chara_mask)
        else:
            star_rail = await AsyncImageFilter.process(star_rail, subclass=ImageFilter.GaussianBlur(20))
            await self._paste_image(star_rail, (0, 0), frost_mask)

        # Frost layer overlay
        frost_layer = Image.new("RGBA", (canvas.width, canvas.height), (0, 0, 0))
        frost_mask = await self._set_transparency(frost_mask, round(0.7 * 255))
        await self._paste_image(frost_layer, (0, 0), frost_mask)

        await self._async_close(mask_data)
        await self._async_close(star_rail)
        await self._async_close(frost_layer)
        await self._async_close(frost_mask)

    async def _create_card_header(self) -> None:
        nickname = self._player.name
        await self._write_text(
            f"UID: {self._player.id}",
            (self.MARGIN + 20, self._canvas.height - self.MARGIN - 20),
            color=(255, 255, 255),
            font_size=24,
            stroke=3,
            stroke_color=(0, 0, 0),
            align="left",
            anchor="ls",
            spacing=6,
        )
        await self._write_text(
            nickname,
            (self.MARGIN + 20, self._canvas.height - self.MARGIN - 55),
            color=(255, 255, 255),
            font_size=30,
            stroke=3,
            stroke_color=(0, 0, 0),
            align="left",
            anchor="ls",
            spacing=6,
        )

    async def _create_canvas_deco(self):
        # Deco 1 - Frost area
        deco1 = await self._async_open(self._images_dir / "MihomoCardDeco.png")
        deco1 = await self._set_transparency(deco1, round(0.5 * 255))
        await self._paste_image(deco1, (0, 0), deco1)
        await self._async_close(deco1)

    async def _create_player_base_info(self) -> None:
        MARGIN_LEFT = 636
        MARGIN_TOP = self.MARGIN + 30
        ICON_SIZE = 64
        ICON_DE = 7

        # If there's no characters, we create a big level/eq level
        if len(self._characters) == 0:
            # Level
            await self._write_text(
                self._i18n.t("mihomo.level") + f": {self._player.level:02d}",
                (MARGIN_LEFT, MARGIN_TOP + 45),
                anchor="ls",
                font_size=40,
                stroke=3,
                stroke_color=self._background,
            )

            # EQ level
            eq_icon = await self._async_open(self._assets_folder / "icon" / "deco" / "IconCompassDeco.png")
            eq_icon = await self._resize_image(eq_icon, (ICON_SIZE, ICON_SIZE))
            await self._paste_image(
                eq_icon,
                (MARGIN_LEFT - ICON_SIZE - ICON_DE, MARGIN_TOP + 60),
                eq_icon,
            )
            await self._write_text(
                self._i18n.t("mihomo.eq_level") + f": {self._player.equilibrium_level}",
                (MARGIN_LEFT, MARGIN_TOP + 105),
                anchor="ls",
                font_size=40,
                stroke=3,
                stroke_color=self._background,
            )
            await self._async_close(eq_icon)
            MARGIN_TOP += 200
        else:
            # If there's a character, we create a small level/eq level
            # And the big chara name, including the level and path.
            main_char = self._characters[0]
            chara_name = self._index_data.characters[main_char.id].name
            chara_level = main_char.level

            # Name
            chara_name_len = await self._write_text(
                chara_name,
                (MARGIN_LEFT, MARGIN_TOP + 45),
                anchor="ls",
                font_size=40,
                stroke=3,
                stroke_color=self._background,
            )
            # Level
            await self._write_text(
                self._i18n.t("chronicles.level_short", [f"{chara_level:02d}"]),
                (MARGIN_LEFT, MARGIN_TOP + 90),
                anchor="ls",
                font_size=30,
                stroke=2,
                stroke_color=self._background,
            )
            # Element
            elem_icon = await self._async_open(self._assets_folder / main_char.element.icon_url)
            elem_icon = await self._resize_image(elem_icon, (ICON_SIZE, ICON_SIZE))
            await self._paste_image(
                elem_icon,
                (MARGIN_LEFT - ICON_SIZE - ICON_DE, MARGIN_TOP + 50),
                elem_icon,
            )
            # Path
            path_icon = await self._async_open(self._assets_folder / main_char.path.icon_url)
            path_icon = await self._resize_image(path_icon, (ICON_SIZE, ICON_SIZE))
            await self._paste_image(
                path_icon,
                (MARGIN_LEFT - ICON_SIZE - ICON_DE, MARGIN_TOP + 50 + ICON_SIZE + 10),
                path_icon,
            )
            await self._async_close(elem_icon)
            await self._async_close(path_icon)

            # Eidolon
            await self._write_text(
                self._i18n.t("mihomo.eidolons") + f": {main_char.eidolon}",
                (MARGIN_LEFT, MARGIN_TOP + 135),
                anchor="ls",
                font_size=30,
                stroke=2,
                stroke_color=self._background,
            )

            # Element/level
            element_name = self._index_data.elements[main_char.element.id].name
            path_name = self._index_data.paths[main_char.path.id].name
            await self._write_text(
                f"{element_name} / {path_name}",
                (MARGIN_LEFT, MARGIN_TOP + 175),
                anchor="ls",
                font_size=28,
                stroke=2,
                stroke_color=self._background,
            )

            # Stars icon (after chara name, left-align)

            star_icon = await self._async_open(self._assets_folder / "icon" / "deco" / "StarBig.png")
            star_icon = await self._resize_image(star_icon, (30, 30))
            for rarity in range(main_char.rarity):
                await self._paste_image(
                    star_icon,
                    (MARGIN_LEFT + round(chara_name_len) + 15 + (rarity * 30), MARGIN_TOP + 20),
                    star_icon,
                )
            await self._async_close(star_icon)

            MARGIN_TOP += 250

        if len(self._characters) > 0:
            # Create player level/eq level first
            ply_level_text = self._i18n.t("mihomo.level") + f": {self._player.level:02d}"
            ply_level_icon = await self._async_open(self._assets_folder / "icon" / "sign" / "CommonTabIcon.png")
            ply_level_icon = await self._resize_image(ply_level_icon, (ICON_SIZE, ICON_SIZE))
            await self._paste_image(
                ply_level_icon,
                (MARGIN_LEFT - ICON_SIZE - ICON_DE, MARGIN_TOP - 42),
                ply_level_icon,
            )
            await self._write_text(
                ply_level_text,
                (MARGIN_LEFT + 2, MARGIN_TOP),
                anchor="ls",
                font_size=30,
                stroke=2,
                stroke_color=self._background,
            )
            await self._async_close(ply_level_icon)
            MARGIN_TOP += 70

            # Create world/eq level
            eq_text = self._i18n.t("mihomo.eq_level") + f": {self._player.equilibrium_level}"
            eq_icon = await self._async_open(self._assets_folder / "icon" / "deco" / "IconCompassDeco.png")
            eq_icon = await self._resize_image(eq_icon, (ICON_SIZE, ICON_SIZE))
            await self._paste_image(
                eq_icon,
                (MARGIN_LEFT - ICON_SIZE - ICON_DE, MARGIN_TOP - 42),
                eq_icon,
            )
            await self._write_text(
                eq_text,
                (MARGIN_LEFT + 2, MARGIN_TOP),
                anchor="ls",
                font_size=30,
                stroke=2,
                stroke_color=self._background,
            )
            await self._async_close(eq_icon)
            MARGIN_TOP += 70

        ## Progression
        progression = self._player.progression

        # Achievements
        achieve_text = self._i18n.t("chronicles.achievements")
        achieve_icon = await self._async_open(self._assets_folder / "icon" / "sign" / "AchievementIcon.png")
        achieve_icon = await self._resize_image(achieve_icon, (ICON_SIZE, ICON_SIZE))
        await self._paste_image(
            achieve_icon,
            (MARGIN_LEFT - ICON_SIZE - ICON_DE, MARGIN_TOP - 42),
            achieve_icon,
        )
        await self._write_text(
            f"{achieve_text}: {progression.achivements:,}",
            (MARGIN_LEFT + 2, MARGIN_TOP),
            anchor="ls",
            font_size=30,
            stroke=2,
            stroke_color=self._background,
        )
        await self._async_close(achieve_icon)
        MARGIN_TOP += 70

        # Characters
        charas_text = self._i18n.t("chronicles.characters")
        charas_icon = await self._async_open(self._assets_folder / "icon" / "sign" / "DataBankAvatarIcon.png")
        charas_icon = await self._resize_image(charas_icon, (ICON_SIZE, ICON_SIZE))
        await self._paste_image(
            charas_icon,
            (MARGIN_LEFT - ICON_SIZE - ICON_DE, MARGIN_TOP - 42),
            charas_icon,
        )
        await self._write_text(
            f"{charas_text}: {progression.avatars:,}",
            (MARGIN_LEFT + 2, MARGIN_TOP),
            anchor="ls",
            font_size=30,
            stroke=2,
            stroke_color=self._background,
        )
        await self._async_close(charas_icon)
        MARGIN_TOP += 70

        # Light cones
        lc_text = self._i18n.t("light_cones")
        lc_icon = await self._async_open(self._assets_folder / "icon" / "sign" / "DataBankLightConeIcon.png")
        lc_icon = await self._resize_image(lc_icon, (ICON_SIZE, ICON_SIZE))
        await self._paste_image(
            lc_icon,
            (MARGIN_LEFT - ICON_SIZE - ICON_DE, MARGIN_TOP - 42),
            lc_icon,
        )
        await self._write_text(
            f"{lc_text}: {progression.light_cones:,}",
            (MARGIN_LEFT + 2, MARGIN_TOP),
            anchor="ls",
            font_size=30,
            stroke=2,
            stroke_color=self._background,
        )
        await self._async_close(lc_icon)
        MARGIN_TOP += 70
        if progression.simulated_universe.value > 0:
            rogue_text = self._i18n.t("rogue")
            rogue_world = self._i18n.t("rogue_world", [str(progression.simulated_universe.value)])
            rogue_icon = await self._async_open(self._assets_folder / "icon" / "sign" / "NoviceRogueIcon.png")
            rogue_icon = await self._resize_image(rogue_icon, (ICON_SIZE, ICON_SIZE))
            await self._paste_image(
                rogue_icon,
                (MARGIN_LEFT - ICON_SIZE - ICON_DE, MARGIN_TOP - 42),
                rogue_icon,
            )
            await self._write_text(
                f"{rogue_text}: {rogue_world}",
                (MARGIN_LEFT + 2, MARGIN_TOP),
                anchor="ls",
                font_size=30,
                stroke=2,
                stroke_color=self._background,
            )
            await self._async_close(rogue_icon)
            MARGIN_TOP += 70
        forgotten_hall = progression.forgotten_hall
        if forgotten_hall and forgotten_hall.finished_floor > 0:
            fh_text = self._i18n.t("abyss")
            fh_floor = self._i18n.t("moc_floor", [str(forgotten_hall.finished_floor)])
            fh_icon = await self._async_open(self._assets_folder / "icon" / "sign" / "AbyssIcon01.png")
            fh_icon = await self._resize_image(fh_icon, (ICON_SIZE, ICON_SIZE))
            await self._paste_image(
                fh_icon,
                (MARGIN_LEFT - ICON_SIZE - ICON_DE, MARGIN_TOP - 42),
                fh_icon,
            )
            await self._write_text(
                f"{fh_text}: {fh_floor}",
                (MARGIN_LEFT + 2, MARGIN_TOP),
                anchor="ls",
                font_size=30,
                stroke=2,
                stroke_color=self._background,
            )
            MARGIN_TOP += 70
        if forgotten_hall.moc_finished_floor > 0:
            moc_text = self._i18n.t("abyss_hard")
            moc_floor = self._i18n.t("moc_floor", [str(forgotten_hall.moc_finished_floor)])
            moc_icon = await self._async_open(self._assets_folder / "icon" / "sign" / "AbyssIcon02.png")
            moc_icon = await self._resize_image(moc_icon, (ICON_SIZE, ICON_SIZE))
            await self._paste_image(
                moc_icon,
                (MARGIN_LEFT - ICON_SIZE - ICON_DE, MARGIN_TOP - 42),
                moc_icon,
            )
            await self._write_text(
                f"{moc_text}: {moc_floor}",
                (MARGIN_LEFT + 2, MARGIN_TOP),
                anchor="ls",
                font_size=30,
                stroke=2,
                stroke_color=self._background,
            )

        # Signature
        if self._player.signature:
            # Put on the left side bottom
            await self._write_text(
                self._player.signature,
                (MARGIN_LEFT, self._canvas.height - self.MARGIN - 30),
                font_size=19,
                stroke=1,
                stroke_color=(0, 0, 0),
                align="left",
                anchor="ls",
                spacing=6,
            )

    async def _calculate_single_starfarer(
        self,
        chara: Character,
    ):
        elem_path_width = 20 + 10 + (50 * 2)
        chara_name = self._index_data.characters[chara.id].name
        char_length = await self._calc_text(chara_name, font_size=32)
        levl_txt = self._i18n.t("chronicles.level_short", [f"{chara.level:02d}"])
        levl_txt_width = await self._calc_text(levl_txt, font_size=18)
        return max(
            char_length + 40,  # Character
            levl_txt_width + 40,  # Level
            elem_path_width + 40,  # Element + Path icon
        )

    async def _create_single_starfarer(
        self,
        chara: Character,
        *,
        margin_left: int,
        margin_top: int,
        max_width: int,
    ):
        chara_icon = await self._async_open(self._assets_folder / chara.icon_url)
        chara_mask = await self._async_open(self._images_dir / "MihomoCardStarfaringMask.png")
        chara_canvas = Image.new("RGBA", (chara_icon.width, chara_icon.height), (0, 0, 0, 255))
        await self._paste_image(
            chara_icon,
            (0, 0),
            chara_mask,
            canvas=chara_canvas,
        )

        chara_canvas = await self._resize_image(chara_canvas, (200, 200))
        await self._paste_image(
            chara_canvas,
            (margin_left, margin_top),
            chara_canvas,
        )
        await self._async_close(chara_icon)
        await self._async_close(chara_mask)
        await self._async_close(chara_canvas)

        # Box
        await self._create_box(
            (
                (margin_left + chara_canvas.width, margin_top),
                (margin_left + chara_canvas.width + max_width, margin_top + chara_canvas.height),
            ),
            color=(*self._background, round(0.5 * 255)),
        )
        # Chara name
        chara_name = self._index_data.characters[chara.id].name
        await self._write_text(
            chara_name,
            (margin_left + chara_canvas.width + 20, margin_top + 50),
            font_size=32,
            stroke=2,
            stroke_color=self._background,
            anchor="ls",
        )
        # Level
        await self._write_text(
            self._i18n.t("chronicles.level_short", [f"{chara.level:02d}"]),
            (margin_left + chara_canvas.width + 20, margin_top + 85),
            font_size=18,
            stroke=2,
            stroke_color=self._background,
            anchor="ls",
        )

        # Path icon
        path_icon = await self._async_open(self._assets_folder / chara.path.icon_url)
        path_icon = await self._resize_image(path_icon, (50, 50))
        await self._paste_image(
            path_icon,
            (margin_left + chara_canvas.width + 20, margin_top + 120),
            path_icon,
        )
        await self._async_close(path_icon)

        # Element
        element_icon = await self._async_open(self._assets_folder / chara.element.icon_url)
        element_icon = await self._resize_image(element_icon, (50, 50))
        await self._paste_image(
            element_icon,
            (margin_left + chara_canvas.width + path_icon.width + 20 + 5, margin_top + 120),
            element_icon,
        )
        await self._async_close(element_icon)

        # Stars icon (max width, right align)
        star_icon = await self._async_open(self._assets_folder / "icon" / "deco" / "StarBig.png")
        star_icon = await self._resize_image(star_icon, (25, 25))
        star_shift = 2
        await self._create_box(
            (
                (
                    star_shift + margin_left + chara_canvas.width - (star_icon.width * chara.rarity) - 10,
                    margin_top + chara_canvas.height - 25 - 6,
                ),
                (
                    star_shift + margin_left + chara_canvas.width - 7,
                    margin_top + chara_canvas.height - 6,
                ),
            ),
            color=(*self._background, round(0.25 * 255)),
        )
        for idx in range(chara.rarity):
            await self._paste_image(
                star_icon,
                (
                    star_shift + margin_left + chara_canvas.width - (star_icon.width * (idx + 1)) - 10,
                    margin_top + chara_canvas.height - 25 - 6,
                ),
                star_icon,
            )
        await self._async_close(star_icon)

        # Eidolons
        await self._write_text(
            f"E{chara.eidolon}",
            (margin_left + 15, margin_top + 15),
            font_size=18,
            stroke=2,
            stroke_color=self._background,
            anchor="ls",
            spacing=10,
        )

    async def _create_starfaring_companions(self) -> None:
        # Only have support or none.
        if len(self._characters) <= 1:
            return

        MARGIN_LEFT = 1500
        MARGIN_TOP = self.MARGIN + 30

        # Starfaring text header
        await self._write_text(
            self._i18n.t(key="mihomo.starfaring"),
            (MARGIN_LEFT, MARGIN_TOP + 45),
            anchor="ls",
            font_size=40,
            stroke=3,
            stroke_color=self._background,
        )
        MARGIN_TOP += 100
        starfarers = self._characters[1:]
        precalculations: list[float] = await asyncio.gather(
            *[self._calculate_single_starfarer(chara) for chara in starfarers]
        )
        max_width = max(precalculations)
        for character in starfarers:
            await self._create_single_starfarer(
                character, margin_left=MARGIN_LEFT, margin_top=MARGIN_TOP, max_width=round(max_width)
            )
            MARGIN_TOP += 250

    async def create(self, **kwargs: Any) -> bytes:
        self._assets_folder = await self._assets_folder.absolute()
        if not await self._assets_folder.exists():
            raise FileNotFoundError("The assets folder does not exist.")
        await self._index_data.async_loads()

        # Create the canvas.
        self.logger.info("Creating canvas...")
        await self._init_canvas()

        self.logger.info("Creating decoration...")
        await self._create_canvas_deco()

        # Create card header.
        self.logger.info("Creating card header...")
        await self._create_card_header()

        # Create player progression.
        self.logger.info("Creating the player progression...")
        await self._create_player_base_info()

        if len(self._characters) > 1:
            self.logger.info("Creating starfaring companions...")
            await self._create_starfaring_companions()

        # Create footer
        self.logger.info("Creating footer...")
        await self._write_text(
            "Supported by Interastral Peace Corporation",
            (self._canvas.width - (self.MARGIN * 2), self._canvas.height - (self.MARGIN * 2)),
            font_size=20,
            alpha=round(0.35 * 255),
            font_path=self._universe_font_path,
            anchor="rs",
            align="right",
        )

        # Save the image.
        bytes_io = await self._async_save_bytes(self._canvas)
        await self._async_close(self._canvas)

        # Return the bytes.
        bytes_io.seek(0)
        all_bytes = await self._loop.run_in_executor(None, bytes_io.read)
        bytes_io.close()
        return all_bytes
