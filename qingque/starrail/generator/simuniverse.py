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

import functools
from typing import TYPE_CHECKING, cast

from PIL import Image

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
from .mixins import (
    SRDrawCharacter,
    StarRailDrawCharacterMixin,
    StarRailDrawDecoMixin,
    StarRailDrawGradientMixin,
)

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


class StarRailSimulatedUniverseCard(
    StarRailDrawGradientMixin, StarRailDrawDecoMixin, StarRailDrawCharacterMixin, StarRailDrawing
):
    MARGIN_LR = 75
    MARGIN_TP = 75

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
            self._foreground = (189, 172, 255)
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
        characters: list[SRDrawCharacter] = [
            SRDrawCharacter.from_hylab(lineup) for lineup in self._record.final_lineups
        ]

        await self._create_character_card(
            characters,
            margin_top=MARGIN_TOP,
            margin_lr=self.MARGIN_LR,
            inbetween_margin=190,
            icon_size=150,
            drawing=self,
        )

        return self.MARGIN_LR + (190 * len(self._record.final_lineups))

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

        default_block_bg = await self._async_open(
            self._assets_folder / "icon" / "rogue" / "room" / "BgRogueDlcChessmanGridUse1.png"
        )

        inbetween_margin = 95
        for idx, strider in enumerate(self._swarm_striders):
            # Icon block
            block_grid_icon = await self._create_swarm_dlc_default_grid(
                default_block_bg,
                strider.type.icon_url,
                offset=-3,
            )
            block_grid_icon = await self._resize_image_side(
                block_grid_icon,
                target=46,
                side="height",
            )
            await self._paste_image(
                block_grid_icon,
                (margin_left + (inbetween_margin * idx), MARGIN_TOP + 30),
                block_grid_icon,
            )
            await self._async_close(block_grid_icon)

            # Create the text box
            draw = await self._get_draw()
            calc_length = await self._calc_text(str(strider.level).zfill(2), font_size=19)
            rounded_rect = functools.partial(
                draw.rounded_rectangle,
                radius=5,
                corners=(False, True, True, False),
                fill=(7, 51, 71),
            )

            await self._loop.run_in_executor(
                None,
                rounded_rect,
                (
                    (
                        margin_left + (inbetween_margin * idx) + block_grid_icon.width,
                        MARGIN_TOP + 41,
                    ),
                    (
                        margin_left + (inbetween_margin * idx) + block_grid_icon.width + 14 + calc_length,
                        MARGIN_TOP + 61,
                    ),
                ),
            )

            # Write the level count
            await self._write_text(
                str(strider.level).zfill(2),
                (margin_left + (inbetween_margin * idx) + block_grid_icon.width + 6, MARGIN_TOP + 58),
                font_size=19,
                anchor="ls",
                color=(255, 255, 255),
            )

    async def _create_boss_icon(self):
        # Composite boss icon
        boss_block_bg = await self._async_open(
            self._assets_folder / "icon" / "rogue" / "room" / "BgRogueDlcChessmanGridBoss.png"
        )
        boss_block_overlay = await self._async_open(
            self._assets_folder / "icon" / "rogue" / "room" / "BgRogueDlcChessmanGridBoss1.png"
        )
        boss_icon = await self._async_open(
            self._assets_folder / "icon" / "rogue" / "room" / "BossIconWhite.png",
        )
        boss_icon = await self._resize_image(boss_icon, (65, 65))

        # Merge them
        boss_width = max(boss_block_bg.width, boss_block_overlay.width)
        boss_height = max(boss_block_bg.height, boss_block_overlay.height)
        boss_canvas = Image.new("RGBA", (boss_width, boss_height), (0, 0, 0, 0))
        await self._paste_image(boss_block_bg, (0, 0), boss_block_bg, canvas=boss_canvas)
        await self._paste_image(boss_block_overlay, (0, 0), boss_block_overlay, canvas=boss_canvas)
        boss_icon_x = (boss_width - boss_icon.width) // 2
        boss_icon_y = ((boss_height - boss_icon.height) // 2) - 5
        await self._paste_image(boss_icon, (boss_icon_x, boss_icon_y), boss_icon, canvas=boss_canvas)

        await self._async_close(boss_block_overlay)
        await self._async_close(boss_icon)

        # Composite boss: swarm icon
        boss_swarm_overlay = await self._async_open(
            self._assets_folder / "icon" / "rogue" / "room" / "BgRogueDlcChessmanGridInSectBoss1.png"
        )
        boss_swarm_icon = await self._async_open(
            self._assets_folder / "icon" / "rogue" / "room" / "BossSwarmIconWhite.png",
        )
        boss_swarm_icon = await self._resize_image(boss_swarm_icon, (75, 75))

        # Merge them
        boss_swarm_width = max(boss_block_bg.width, boss_swarm_overlay.width)
        boss_swarm_height = max(boss_block_bg.height, boss_swarm_overlay.height)
        boss_swarm_canvas = Image.new("RGBA", (boss_swarm_width, boss_swarm_height), (0, 0, 0, 0))
        await self._paste_image(boss_block_bg, (0, 0), boss_block_bg, canvas=boss_swarm_canvas)
        await self._paste_image(boss_swarm_overlay, (0, 0), boss_swarm_overlay, canvas=boss_swarm_canvas)
        boss_swarm_icon_x = (boss_swarm_width - boss_swarm_icon.width) // 2
        boss_swarm_icon_y = (boss_swarm_height - boss_swarm_icon.height) // 2
        await self._paste_image(
            boss_swarm_icon, (boss_swarm_icon_x, boss_swarm_icon_y), boss_swarm_icon, canvas=boss_swarm_canvas
        )

        await self._async_close(boss_block_bg)
        await self._async_close(boss_swarm_overlay)
        await self._async_close(boss_swarm_icon)

        return boss_canvas, boss_swarm_canvas

    async def _create_swarm_dlc_default_grid(
        self,
        block_bg: Image.Image,
        block_icon_path: str,
        block_color: str = "#FFFFFF",
        offset: int = 0,
    ):
        icon_block_path = self._assets_folder / block_icon_path
        block_icon = await self._async_open(self._assets_folder / icon_block_path)
        icon_block_col = hex_to_rgb(block_color)
        if icon_block_col and icon_block_col != (255, 255, 255):
            # Tint if needed
            block_icon = await self._tint_image(block_icon, icon_block_col)

        canvas = Image.new("RGBA", (block_bg.width, block_bg.height), (0, 0, 0, 0))
        await self._paste_image(block_bg, (0, 0), block_bg, canvas=canvas)

        block_icon = await self._resize_image(block_icon, (70, 70))
        icon_x = (block_bg.width - block_icon.width) // 2
        icon_y = ((block_bg.height - block_icon.height) // 2) + offset
        await self._paste_image(block_icon, (icon_x, icon_y), block_icon, canvas=canvas)
        await self._async_close(block_icon)
        return canvas

    async def _create_swarm_domain_type(self, margin_left: int):
        if not isinstance(self._record, ChronicleRogueLocustDetailRecord):
            return

        MARGIN_TOP = self.MARGIN_TP + 240
        if self._swarm_striders:
            MARGIN_TOP += 90

        await self._write_text(
            self._i18n.t("chronicles.rogue.locust_domain"),
            (margin_left, MARGIN_TOP + 16),
            font_size=20,
            anchor="ls",
        )

        inbetween_margin = 90
        boss_blocks = [11, 12]
        has_boss_blocks = any(x.id in boss_blocks for x in self._record.blocks if x.count > 0)

        default_block_bg = await self._async_open(
            self._assets_folder / "icon" / "rogue" / "room" / "BgRogueDlcChessmanGridMove1.png"
        )

        grid_chess_icons: dict[int, Image.Image] = {}
        if has_boss_blocks:
            boss_canvas, boss_swarm_canvas = await self._create_boss_icon()
            grid_chess_icons[11] = boss_canvas
            grid_chess_icons[12] = boss_swarm_canvas

        # Split block into 7 and 7
        block_splits = [self._record.blocks[x : x + 7] for x in range(0, len(self._record.blocks), 7)]

        for block_split in block_splits:
            for idx, block in enumerate(block_split):
                block_info = self._index_data.swarmdlc_blocks[str(block.id)]
                # Icon block
                block_grid_icon = grid_chess_icons.get(block.id) or await self._create_swarm_dlc_default_grid(
                    default_block_bg, block_info.icon_url.replace(".png", "White.png"), block_info.color
                )
                block_grid_icon = await self._resize_image_side(
                    block_grid_icon,
                    target=46,
                    side="height",
                )
                await self._paste_image(
                    block_grid_icon,
                    (margin_left + (inbetween_margin * idx), MARGIN_TOP + 30),
                    block_grid_icon,
                )
                await self._async_close(block_grid_icon)

                # Create the text box
                draw = await self._get_draw()
                calc_length = await self._calc_text(str(block.count).zfill(2), font_size=19)
                rounded_rect = functools.partial(
                    draw.rounded_rectangle,
                    radius=5,
                    corners=(False, True, True, False),
                    fill=(71, 59, 155) if block_info.id not in boss_blocks else (102, 33, 46),
                )

                await self._loop.run_in_executor(
                    None,
                    rounded_rect,
                    (
                        (
                            margin_left + (inbetween_margin * idx) + block_grid_icon.width,
                            MARGIN_TOP + 41,
                        ),
                        (
                            margin_left + (inbetween_margin * idx) + block_grid_icon.width + 14 + calc_length,
                            MARGIN_TOP + 61,
                        ),
                    ),
                )

                # Write the visit count
                await self._write_text(
                    str(block.count).zfill(2),
                    (margin_left + (inbetween_margin * idx) + block_grid_icon.width + 6, MARGIN_TOP + 58),
                    font_size=19,
                    anchor="ls",
                    color=(255, 255, 255),
                )
            MARGIN_TOP += 50
        await self._async_close(default_block_bg)

    async def create(self, *, hide_credits: bool = False, hide_timestamp: bool = False) -> bytes:
        self._assets_folder = await self._assets_folder.absolute()
        if not await self._assets_folder.exists():
            raise FileNotFoundError("The assets folder does not exist.")
        await self._index_data.async_loads()

        # Precalculate blessings and curios height so we can extend the canvas.
        self.logger.info("Precalculating blessings and curios...")
        await self._precalculate_blessings_and_curios()

        # Decoration
        self.logger.info("Creating decoration...")
        await self._create_decoration(hide_credits, drawing=self)

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
