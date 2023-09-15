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

from typing import TYPE_CHECKING, ClassVar, cast

from qingque.hylab.models.simuniverse import (
    ChronicleRogueBlessingItem,
    ChronicleRogueCurio,
    ChronicleRogueLocustDetailRecord,
    ChronicleRogueLocustOverviewDestiny,
    ChronicleRoguePeriodRun,
    ChronicleRogueUserInfo,
)
from qingque.i18n import get_roman_numeral
from qingque.mihomo.models.constants import MihomoLanguage
from qingque.tooling import get_logger
from qingque.utils import strip_unity_rich_text

from .base import RGB, StarRailDrawing, StarRailDrawingLogger

if TYPE_CHECKING:
    from qingque.hylab.models.base import HYLanguage
    from qingque.i18n import QingqueLanguage
    from qingque.starrail.loader import SRSDataLoader

__all__ = ("StarRailSimulatedUniverseCard",)


def _text_fixup(text: str):
    text = strip_unity_rich_text(text)
    text = text.replace("≪", "<<")
    text = text.replace("≫", ">>")
    return text


def hex_to_rgb(hex_str: str) -> RGB | None:
    hex_str = hex_str.lstrip("#")
    if not hex_str:
        return None
    rgb = tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))
    return cast(RGB, rgb)


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
        swarm_striders: list[ChronicleRogueLocustOverviewDestiny] | None = None,
        *,
        language: MihomoLanguage | HYLanguage | QingqueLanguage = MihomoLanguage.EN,
        loader: SRSDataLoader | None = None,
    ) -> None:
        super().__init__(language=language, loader=loader)
        self._record = record
        self._user = user
        self._swarm_striders = swarm_striders or []
        self.logger = get_logger(
            "qingque.starrail.generator.simuniverse",
            adapter=StarRailDrawingLogger.create(f"{self._user.name}-{type(record).__name__}—{self._record.name}"),
        )
        if isinstance(self._record, ChronicleRogueLocustDetailRecord):
            self._background = (26, 27, 51)
            self._foreground = (250, 250, 250)
        else:
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
                    (self.MARGIN_LR + (inbetween_margin * idx) + chara_icon.width - 31, MARGIN_TOP),
                    (self.MARGIN_LR + (inbetween_margin * idx) + chara_icon.width - 1, MARGIN_TOP + 30),
                ),
                color=(*self._foreground, round(0.8 * 255)),
            )
            # Write the eidolon
            await self._write_text(
                f"E{lineup.eidolons}",
                (self.MARGIN_LR + (inbetween_margin * idx) + chara_icon.width - 16, MARGIN_TOP + 22),
                font_size=20,
                anchor="ms",
                color=self._background,
            )
            # Create the element icon
            await self._create_circle(
                [
                    self.MARGIN_LR + (inbetween_margin * idx) + 2,
                    MARGIN_TOP + 2,
                    self.MARGIN_LR + (inbetween_margin * idx) + 33,
                    MARGIN_TOP + 33,
                ],
                color=(*self._background, 128),
                width=0,
            )
            element_icon = await self._async_open(self._assets_folder / lineup.element.icon_url)
            element_icon = await self._resize_image(element_icon, (28, 28))
            # Paste Top-left corner
            await self._paste_image(
                element_icon,
                (self.MARGIN_LR + (inbetween_margin * idx) + 3, MARGIN_TOP + 3),
                element_icon,
            )
            await self._async_close(element_icon)
            await self._async_close(chara_icon)
        return self.MARGIN_LR + (inbetween_margin * len(self._record.final_lineups))

    async def _create_decoration(self, hide_credits: bool = False) -> None:
        # DialogFrameDeco1.png (orig 395x495)

        deco_top_right = await self._async_open(
            self._assets_folder / "icon" / "deco" / "DecoShortLineRing177R@3x.png",
        )
        deco_top_right = await self._tint_image(deco_top_right, self._foreground)
        await self._paste_image(
            deco_top_right,
            (self._canvas.width - deco_top_right.width, 0),
            deco_top_right,
        )

        deco_bot_left = await self._async_open(
            self._assets_folder / "icon" / "deco" / "DialogFrameDeco1.png",
        )
        deco_bot_left = await self._tint_image(deco_bot_left, self._foreground)
        deco_bot_left = await self._resize_image(deco_bot_left, (160, 200))
        await self._paste_image(
            deco_bot_left,
            (0, self._canvas.height - deco_bot_left.height),
            deco_bot_left,
        )

        deco_bot_right = await self._async_open(
            self._assets_folder / "icon" / "deco" / "DialogFrameDeco1@3x.png",
        )
        deco_bot_right = await self._tint_image(deco_bot_right, self._foreground)
        deco_bot_right_mid = (deco_bot_right.height // 2) - (deco_bot_right.height // 6)

        await self._paste_image(
            deco_bot_right,
            (
                self._canvas.width - deco_bot_right.width + deco_bot_right_mid,
                self._canvas.height - deco_bot_right.height + deco_bot_right_mid,
            ),
            deco_bot_right,
        )

        # Bottom middle
        deco_bot_mid = await self._async_open(self._assets_folder / "icon" / "deco" / "NewSystemDecoLine.png")
        deco_bot_mid = await self._tint_image(deco_bot_mid, self._foreground)
        # 360 x 48, put in the middle with 25 padding

        deco_bot_mid_vert_box = self._canvas.height - deco_bot_mid.height - 35
        if not hide_credits:
            deco_bot_mid_vert_box -= 10
        await self._paste_image(
            deco_bot_mid,
            (
                (self._canvas.width // 2) - (deco_bot_mid.width // 2),
                deco_bot_mid_vert_box,
            ),
            deco_bot_mid,
        )

        # Close all images
        await self._async_close(deco_top_right)
        await self._async_close(deco_bot_left)
        await self._async_close(deco_bot_right)
        await self._async_close(deco_bot_mid)

    async def _precalculate_blessings_and_curios(self):
        if len(self._record.blessings) > 0:
            MARGIN_TOP = self.MARGIN_TP + 450
            ICON_SIZE = 50
            MAX_WIDTH = self._canvas.width - self.MARGIN_LR - (ICON_SIZE * 2) - 60
            TEXT_SIZE = 20
            TEXT_MARGIN = 13

            for blessing_info in self._record.blessings:
                _temp_nested_blessings = []
                _temp_current_length = 0
                blessings = blessing_info.items
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

                for _ in nested_blessings:
                    MARGIN_TOP += 30
                MARGIN_TOP -= 30
                MARGIN_TOP += 65
        else:
            MARGIN_TOP = self.MARGIN_TP

        if len(self._record.curios) > 0:
            MARGIN_TOP += 55
            EXTRA_MARGIN = 10
            ICON_SIZE = 50
            ICON_MARGIN = 10
            MAX_WIDTH = self._canvas.width - self.MARGIN_LR - ICON_MARGIN

            nested_curios: list[list[ChronicleRogueCurio]] = []
            _temp_curios = []
            _counter = 0
            for curio in self._record.curios:
                calc_length = (_counter * ICON_SIZE) + (_counter * ICON_MARGIN)
                if self.MARGIN_LR + calc_length >= MAX_WIDTH:
                    nested_curios.append(_temp_curios)
                    _temp_curios = []
                    _counter = 0
                _temp_curios.append(curio)
                _counter += 1
            if _temp_curios:
                nested_curios.append(_temp_curios)

            for _ in nested_curios:
                MARGIN_TOP += ICON_SIZE + ICON_MARGIN
            MARGIN_TOP -= ICON_SIZE + ICON_MARGIN
            MARGIN_TOP += EXTRA_MARGIN

            # Automatic extend down
            canvas_max = self._canvas.height - self.MARGIN_TP
            bottom_part = MARGIN_TOP + 65
            if bottom_part >= canvas_max:
                # We need to extend the canvas.
                extended = bottom_part - canvas_max
                if extended < 0:
                    extended = canvas_max - bottom_part
                await self._extend_canvas_down(int(round(extended)))

    async def _create_obtained_blessings(self) -> float:
        MARGIN_TOP = self.MARGIN_TP + 450
        ICON_SIZE = 50
        MAX_WIDTH = self._canvas.width - self.MARGIN_LR - (ICON_SIZE * 2) - 60
        TEXT_SIZE = 20
        TEXT_MARGIN = 13

        # Precheck blessings
        if len(self._record.blessings) < 1:
            return self.MARGIN_TP

        emptyness = []
        for blessing_info in self._record.blessings:
            emptyness.append(len(blessing_info.items) > 0)
        # Check if all are emptyness is False
        if not any(emptyness):
            return self.MARGIN_TP

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

    async def _create_obtained_curios(self, margin_top: float) -> float:
        if len(self._record.curios) < 1:
            return margin_top
        # Text header
        await self._write_text(
            self._i18n.t("chronicles.rogue.curios"),
            (self.MARGIN_LR, margin_top + 30),
            font_size=20,
            anchor="ls",
        )

        EXTRA_MARGIN = 10
        MARGIN_TOP = margin_top + 55
        if len(self._record.blessings) < 1:
            MARGIN_TOP = self.MARGIN_TP
        ICON_SIZE = 50
        ICON_MARGIN = 10
        MAX_WIDTH = self._canvas.width - self.MARGIN_LR - ICON_MARGIN

        # We will create it into a nested blessings first before writing it.
        nested_curios: list[list[ChronicleRogueCurio]] = []
        _temp_curios = []
        _counter = 0
        for curio in self._record.curios:
            calc_length = (_counter * ICON_SIZE) + (_counter * ICON_MARGIN)
            if self.MARGIN_LR + calc_length >= MAX_WIDTH:
                nested_curios.append(_temp_curios)
                _temp_curios = []
                _counter = 0
            _temp_curios.append(curio)
            _counter += 1
        if _temp_curios:
            nested_curios.append(_temp_curios)

        for curio_nest in nested_curios:
            for idx, curio in enumerate(curio_nest):
                # Open the image
                curio_info = self._index_data.simuniverse_curios[str(curio.id)]
                curio_icon = await self._async_open(self._assets_folder / curio_info.icon_url)
                # Resize
                curio_icon = await self._resize_image(curio_icon, (ICON_SIZE, ICON_SIZE))
                # Paste
                marg_length = self.MARGIN_LR + (idx * ICON_SIZE) + (idx * ICON_MARGIN)
                await self._paste_image(
                    curio_icon,
                    (marg_length, MARGIN_TOP),
                    curio_icon,
                )
                await self._async_close(curio_icon)
            MARGIN_TOP += ICON_SIZE + ICON_MARGIN
        MARGIN_TOP -= ICON_SIZE + ICON_MARGIN
        return MARGIN_TOP + EXTRA_MARGIN

    async def _create_swarm_pathstrider(self, margin_left: int):
        if not isinstance(self._record, ChronicleRogueLocustDetailRecord):
            return
        if not self._swarm_striders:
            return

        MARGIN_TOP = self.MARGIN_TP + 240

        await self._write_text(
            self._i18n.t("chronicles.rogue.locust_narrow"),
            (margin_left, MARGIN_TOP + 16),
            font_size=20,
            anchor="ls",
        )

        inbetween_margin = 100
        for idx, strider in enumerate(self._swarm_striders):
            text_len = await self._calc_text(str(strider.level).zfill(2), font_size=20)
            # Create box
            await self._create_box(
                (
                    (margin_left + (inbetween_margin * idx), MARGIN_TOP + 30),
                    (margin_left + (inbetween_margin * idx) + 50 + text_len, MARGIN_TOP + 30 + 30),
                ),
                color=(189, 172, 255, round(0.25 * 255)),
            )

            icon_destiny = await self._async_open(self._assets_folder / strider.type.icon_url)
            icon_destiny = await self._resize_image(icon_destiny, (25, 25))
            await self._paste_image(
                icon_destiny,
                (margin_left + (inbetween_margin * idx) + 4, MARGIN_TOP + 33),
                icon_destiny,
            )
            await self._async_close(icon_destiny)
            await self._write_text(
                str(strider.level).zfill(2),
                (margin_left + (inbetween_margin * idx) + 50, MARGIN_TOP + 46),
                font_size=20,
                anchor="mm",
                color=(255, 255, 255),
                alpha=round(0.75 * 255),
            )

    async def _create_swarm_domain_type(self, margin_left: int):
        if not isinstance(self._record, ChronicleRogueLocustDetailRecord):
            return

        MARGIN_TOP = self.MARGIN_TP + 240
        if self._swarm_striders:
            MARGIN_TOP += 80

        await self._write_text(
            self._i18n.t("chronicles.rogue.locust_domain"),
            (margin_left, MARGIN_TOP + 16),
            font_size=20,
            anchor="ls",
        )

        inbetween_margin = 90
        boss_color = (61, 21, 29, round(0.8 * 255))
        default_color = (189, 172, 255, round(0.25 * 255))
        boss_blocks = [11, 12]
        for idx, block in enumerate(self._record.blocks):
            block_info = self._index_data.swarmdlc_blocks[str(block.id)]
            text_len = await self._calc_text(str(block.count).zfill(2), font_size=20)
            # Create box
            await self._create_box(
                (
                    (margin_left + (inbetween_margin * idx), MARGIN_TOP + 30),
                    (margin_left + (inbetween_margin * idx) + 50 + text_len, MARGIN_TOP + 30 + 30),
                ),
                color=boss_color if block_info.id in boss_blocks else default_color,
            )

            # Icon block
            icon_block_path = self._assets_folder / block_info.icon_url
            icon_blocks = await self._async_open(icon_block_path.with_stem(icon_block_path.stem + "White"))
            icon_block_col = hex_to_rgb(block_info.color)
            if icon_block_col and icon_block_col != (255, 255, 255):
                # Tint if needed
                icon_blocks = await self._tint_image(icon_blocks, icon_block_col)
            icon_blocks = await self._resize_image(icon_blocks, (25, 25))
            await self._paste_image(
                icon_blocks,
                (margin_left + (inbetween_margin * idx) + 4, MARGIN_TOP + 33),
                icon_blocks,
            )
            await self._async_close(icon_blocks)
            await self._write_text(
                str(block.count).zfill(2),
                (margin_left + (inbetween_margin * idx) + 50, MARGIN_TOP + 46),
                font_size=20,
                anchor="mm",
                color=(255, 255, 255),
                alpha=round(0.75 * 255),
            )

    async def create(self, *, hide_credits: bool = False, hide_timestamp: bool = False):
        self._assets_folder = await self._assets_folder.absolute()
        if not await self._assets_folder.exists():
            raise FileNotFoundError("The assets folder does not exist.")
        await self._index_data.async_loads()

        # Precalculate blessings and curios height so we can extend the canvas.
        self.logger.info("Precalculating blessings and curios...")
        await self._precalculate_blessings_and_curios()

        # Decoration
        self.logger.info("Creating decoration...")
        await self._create_decoration(hide_credits=hide_credits)

        # Write the world header
        self.logger.info("Writing world header...")
        await self._create_world_header()

        # Create the character used.
        self.logger.info("Writing character profile...")
        profile_right = await self._create_character_profile()

        # Create blessings
        self.logger.info("Writing obtained blessings...")
        obtain_max = await self._create_obtained_blessings()

        # Create curios
        self.logger.info("Writing obtained curios...")
        await self._create_obtained_curios(obtain_max)

        if isinstance(self._record, ChronicleRogueLocustDetailRecord):
            self.logger.info("Writing swarm pathstrider...")
            await self._create_swarm_pathstrider(profile_right)
            self.logger.info("Writing swarm domain type...")
            await self._create_swarm_domain_type(profile_right)

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
        if not hide_credits:
            await self._write_text(
                self._i18n.t("chronicles.credits"),
                (self._canvas.width // 2, self._canvas.height - 20),
                font_size=16,
                alpha=128,
                anchor="ms",
            )
        if not hide_timestamp:
            # DateTime are in UTC+8
            dt = self._record.end_time.datetime
            # Format to Day, Month YYYY HH:MM
            fmt_timestamp = dt.strftime("%a, %b %d %Y %H:%M")
            await self._write_text(
                f"{fmt_timestamp} UTC+8",
                (20, 20),
                font_size=20,
                anchor="lt",
                align="left",
                alpha=round(0.35 * 255),
            )

        # Save the image.
        self.logger.info("Saving the image...")
        bytes_io = await self._async_save_bytes(self._canvas)

        self.logger.info("Cleaning up...")
        await self._async_close(self._canvas)

        # Return the bytes.
        bytes_io.seek(0)
        all_bytes = await self._loop.run_in_executor(None, bytes_io.read)
        bytes_io.close()
        return all_bytes
