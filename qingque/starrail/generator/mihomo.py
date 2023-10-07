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

from typing import TYPE_CHECKING, TypeAlias, cast

from aiopath import AsyncPath
from PIL import Image

from qingque.mihomo.models.base import MihomoBase
from qingque.mihomo.models.characters import Character
from qingque.mihomo.models.combats import ElementType, SkillTrace, SkillUsageType
from qingque.mihomo.models.constants import MihomoLanguage
from qingque.mihomo.models.player import PlayerInfo
from qingque.mihomo.models.relics import Relic, RelicSet
from qingque.mihomo.models.stats import StatsAtrributes, StatsField, StatsProperties, StatsPropertiesAffix
from qingque.models.region import HYVServer
from qingque.starrail.models.relics import SRSRelicType
from qingque.starrail.models.stats import SRSProperties
from qingque.starrail.scoring import RelicScores, RelicScoring, RelicScoringNoSuchCharacterException
from qingque.tooling import get_logger

from .base import RGB, StarRailDrawing, StarRailDrawingLogger

if TYPE_CHECKING:
    from qingque.hylab.models import HYLanguage
    from qingque.i18n import PartialTranslate, QingqueI18n, QingqueLanguage
    from qingque.starrail.loader import SRSDataLoader

__all__ = (
    "get_mihomo_dominant_color",
    "SRSCardStats",
    "StarRailMihomoCard",
)

_COLOR_DOMINANT: dict[str, RGB | list[RGB]] = {
    "1001": [(230, 160, 205), (202, 253, 250)],
    "1002": (155, 89, 83),
    "1003": [(191, 42, 48), (212, 192, 210)],
    "1004": (88, 85, 82),
    "1005": (67, 52, 63),
    "1006": (43, 65, 112),
    "1008": (59, 61, 100),
    "1009": [(132, 94, 115), (197, 169, 210)],
    "1013": (71, 58, 85),
    "1101": [(34, 58, 137), (104, 188, 181)],
    "1102": [(78, 53, 161), (218, 231, 255)],
    "1103": (53, 49, 68),
    "1104": (70, 83, 139),
    "1105": (181, 172, 159),
    "1106": (57, 85, 151),
    "1107": (63, 57, 82),
    "1108": (96, 90, 136),
    "1109": [(190, 144, 54), (252, 235, 149)],
    "1110": (34, 83, 172),
    "1111": [(130, 25, 45), (220, 206, 199)],
    "1112": [(173, 46, 92), (246, 194, 98)],
    "1201": (55, 86, 93),
    "1202": [(239, 211, 148), (206, 60, 49)],
    "1203": (81, 99, 93),
    "1204": (201, 186, 170),
    "1205": (69, 52, 62),
    "1206": (204, 200, 188),
    "1207": [(144, 163, 152), (55, 86, 93)],
    "1208": [(77, 54, 91), (230, 131, 204)],
    "1209": (49, 109, 173),
    "1210": [(255, 166, 132), (129, 21, 39)],
    "1211": [(75, 102, 163), (205, 176, 219)],
    "1212": [(16, 22, 75), (178, 213, 254)],
    "1213": [(34, 42, 46), (94, 255, 255)],
    "8001": (48, 44, 62),
    "8002": (48, 44, 62),
    "8003": [(234, 149, 56), (49, 42, 42)],
    "8004": [(234, 149, 56), (49, 42, 42)],
}
_MetaStats: TypeAlias = dict[StatsField, int | float]


def get_mihomo_dominant_color(character_id: str | int) -> RGB | None:
    color = _COLOR_DOMINANT.get(str(character_id))
    if color is None:
        return None
    if isinstance(color, list):
        return color[0]
    return color


def _get_player_server(server: HYVServer, i18n: PartialTranslate) -> str:
    match server:
        case HYVServer.ChinaA | HYVServer.ChinaB | HYVServer.ChinaC:
            return i18n("region.short.china")
        case HYVServer.NorthAmerica:
            return i18n("region.short.na")
        case HYVServer.Europe:
            return i18n("region.short.eur")
        case HYVServer.Asia:
            return i18n("region.short.asia")
        case HYVServer.Taiwan:
            return i18n("region.short.taiwan")


# Sizing:
#  - Path: 80x80
#  - Element: 80x80
#  - Chara: 374x312 (Original: 374x512, we will crop the bottom part)
#  - Stats Icon: 20x20
#  - Relics Icon: 128x128 (Original 256x256, but we will make it smaller than 128x128 like 96x96 and center it)
#  - Skill Icon: 96x96
# Starting point:
#  - Top: 184
#  - Left: 62
#  - Right: 1506
#  - Bottom: 830


class SRSCardStats(MihomoBase, frozen=True):
    name: str
    icon_url: str | None = None
    value: int | float | None = None
    percent: bool = False
    cut_off: bool = False
    count: int = -1

    @classmethod
    def from_relic(
        cls: type[SRSCardStats],
        relic: StatsProperties | StatsAtrributes | StatsPropertiesAffix,
        cut_off: bool = False,
        *,
        i18n: QingqueI18n,
    ) -> "SRSCardStats":
        roll_count = -1
        if isinstance(relic, StatsPropertiesAffix):
            roll_count = relic.count
        relic_name = i18n.t(f"mihomo.stats_simple.{relic.field.value}")
        return cls(
            name=relic_name,
            icon_url=relic.icon_url,
            value=relic.value,
            percent=relic.percent,
            cut_off=cut_off,
            count=roll_count,
        )


class StarRailMihomoCard(StarRailDrawing):
    CHARACTER_TOP = 164
    CHARACTER_BOTTOM = CHARACTER_TOP + 352
    CHARACTER_LEFT = 1006
    CHARACTER_RIGHT = CHARACTER_LEFT + 500

    RELIC_LEFT = 62

    def __init__(
        self,
        character: Character,
        player: PlayerInfo,
        *,
        language: MihomoLanguage | QingqueLanguage | HYLanguage = MihomoLanguage.EN,
        loader: SRSDataLoader | None = None,
        relic_scorer: RelicScoring | None = None,
    ) -> None:
        super().__init__(language=language, loader=loader)
        self.logger = get_logger(
            "qingque.starrail.generator.mihomo",
            adapter=StarRailDrawingLogger.create(f"UID-{player.id}/C-{character.id}"),
        )
        self._player: PlayerInfo = player
        self._character: Character = character

        # Initialize the card canvas.
        # Inner canvas is 1568x910
        self._make_canvas(width=1568, height=910)
        self._stats_fields_to_props: dict[StatsField, SRSProperties] = {}
        self._relic_scorer: RelicScoring = relic_scorer or RelicScoring(
            self._assets_folder / ".." / "relic_scores.json"
        )

    def is_trailblazer(self):
        return int(self._character.id) >= 8001

    def _get_element(self, element: ElementType) -> AsyncPath:
        elem_txt = element.name
        if elem_txt == "Thunder":
            elem_txt = "Lightning"
        element_path = self._assets_folder / "icon" / "element" / f"{elem_txt}White.png"
        return element_path

    async def _create_character_card_header(self) -> None:
        # Load the character preview image.
        preview_path = self._assets_folder / self._character.preview_url
        preview_image = await self._async_open(preview_path)

        # Write the character name.
        chara_data = self._index_data.characters[self._character.id]
        chara_name = chara_data.name
        if "{NICKNAME}" in chara_name:
            tb_name_tl = "mihomo.tb_name" if chara_data.tag.startswith("playerboy") else "mihomo.tb_name_female"
            chara_name = self._i18n.t(tb_name_tl, [self._player.name])
        await self._write_text(
            chara_name,
            (self.CHARACTER_RIGHT - 4, self.CHARACTER_TOP - 30),
            font_size=46,
            anchor="rs",
            align="right",
        )

        # Crop the bottom part of the image.
        _pr_top_crop = 20
        _pr_bot_crop = preview_image.height - 342 + _pr_top_crop
        preview_image = await self._crop_image(
            preview_image,
            (0, _pr_top_crop, preview_image.width, preview_image.height - _pr_bot_crop),
        )

        # Start: 1006, 184
        # End: 1506, 536
        # Using the above number, create a rectangle with foreground color.
        await self._create_box(
            ((self.CHARACTER_LEFT, self.CHARACTER_TOP), (self.CHARACTER_RIGHT, self.CHARACTER_BOTTOM)),
        )

        # Put the preview image on the canvas, shift by 4px to the right and bottom.
        await self._paste_image(preview_image, (self.CHARACTER_LEFT + 4, self.CHARACTER_TOP + 4), preview_image)

        # Write the Level text
        # Pad: 14px, y: center between image and bottom
        await self._write_text(
            self._i18n.t("mihomo.level"),
            (self.CHARACTER_LEFT + 14, self.CHARACTER_BOTTOM - 22),
            font_size=24,
            color=self._background,
            anchor="lm",
            align="left",
        )

        # Write the Level number
        await self._write_text(
            str(self._character.level).zfill(2),
            (self.CHARACTER_RIGHT - 14, self.CHARACTER_BOTTOM - 22),
            font_size=24,
            color=self._background,
            anchor="rm",
            align="right",
        )

        # Element image
        element_img = await self._async_open(self._get_element(self._character.element.id))
        element_img = await self._tint_image(element_img, self._background)
        element_img = await self._resize_image(element_img, (96, 96))
        await self._paste_image(element_img, (self.CHARACTER_RIGHT - 108, self.CHARACTER_TOP + 64), element_img)

        # Write the character trailblaze path
        path_img = await self._async_open(self._assets_folder / self._character.path.icon_url)
        path_img = await self._tint_image(path_img, self._background)
        path_img = await self._resize_image(path_img, (96, 96))
        await self._paste_image(
            path_img,
            (self.CHARACTER_RIGHT - 108, self.CHARACTER_TOP + 176),
            path_img,
        )

        # Write text at top-right of the rectangle for Element / Path
        element_name = self._index_data.elements[self._character.element.id].name
        path_name = self._index_data.paths[self._character.path.id].name
        elem_path_width = await self._calc_text(
            f"{element_name} / {path_name}",
            font_size=20,
        )
        # Create a box for the text
        await self._create_box(
            (
                (self.CHARACTER_RIGHT - elem_path_width - 6, self.CHARACTER_TOP),
                (self.CHARACTER_RIGHT, self.CHARACTER_TOP + 32),
            ),
            color=(*self._foreground, round(0.75 * 255)),
        )
        await self._write_text(
            f"{element_name} / {path_name}",
            (self.CHARACTER_RIGHT - 4, self.CHARACTER_TOP + 22),
            font_size=20,
            color=self._background,
            anchor="rs",
            align="right",
        )

        # Put the rarity stars
        stars_icon = await self._async_open(self._assets_folder / "icon" / "deco" / "StarBig_WhiteGlow.png")
        stars_icon = await self._tint_image(stars_icon, self._background)
        stars_icon = await self._resize_image(stars_icon, (24, 24))
        star_right_start = self.CHARACTER_RIGHT - 24 - 4
        top_marg_star = self.CHARACTER_TOP + 20 + 12
        for idx in range(self._character.rarity):
            # Every 24px, we want to put the star from right to left.
            await self._paste_image(
                stars_icon,
                (star_right_start - (idx * 24), top_marg_star),
                stars_icon,
            )

        # Close all images
        await self._async_close(preview_image)
        await self._async_close(element_img)
        await self._async_close(path_img)
        await self._async_close(stars_icon)

    async def _combine_character_stats(self) -> _MetaStats:
        stats_meta: dict[StatsField, int | float] = {
            StatsField.HP: 1,
            StatsField.ATK: 1,
            StatsField.DEF: 1,
            StatsField.Speed: 1,
            StatsField.CritRate: 0.0,
            StatsField.CritDamage: 0.0,
            StatsField.BreakEffect: 0.0,
            StatsField.HealingRate: 0.0,
            StatsField.EnergyRegenRate: 1.0,
            StatsField.EffectHitRate: 0.0,
            StatsField.EffectResist: 0.0,
            StatsField.PhysicalBoost: 0.0,
            StatsField.FireBoost: 0.0,
            StatsField.IceBoost: 0.0,
            StatsField.LightningBoost: 0.0,
            StatsField.WindBoost: 0.0,
            StatsField.QuantumBoost: 0.0,
            StatsField.ImaginaryBoost: 0.0,
            StatsField.DamageBoost: 0.0,
            StatsField.PhysicalResist: 0.0,
            StatsField.FireResist: 0.0,
            StatsField.IceResist: 0.0,
            StatsField.LightningResist: 0.0,
            StatsField.WindResist: 0.0,
            StatsField.QuantumResist: 0.0,
            StatsField.ImaginaryResist: 0.0,
        }
        # Do the stats calculation here.
        for stats in self._character.attributes:
            stats_meta[stats.field] += stats.value
        for stats in self._character.additions:
            stats_meta[stats.field] += stats.value
        return stats_meta

    async def _create_character_stats(self) -> None:
        size = 32
        starting_top = self.CHARACTER_BOTTOM - 22
        left_start = 1006
        right_start = 1506
        index_icon = 1
        stats_meta = await self._combine_character_stats()
        valid_meta_entries = {k: v for k, v in stats_meta.items() if v > 0.0}
        # Check if it's more than 10 entries, if it's extend the canvas.
        if len(valid_meta_entries) > 10:
            await self._extend_canvas_down((len(valid_meta_entries) - 10) * (size + 2))
        non_percentage = [StatsField.HP, StatsField.ATK, StatsField.DEF, StatsField.Speed]
        for stats_field, stats_value in valid_meta_entries.items():
            if stats_value <= 0.0:
                continue
            stats_info = self._stats_fields_to_props[stats_field]

            # Stats icon
            stats_icon = await self._async_open(self._assets_folder / stats_info.icon_url)
            # Tint icon
            stats_icon = await self._tint_image(stats_icon, self._foreground)
            # Resize icon
            stats_icon = await self._resize_image(stats_icon, (size, size))

            # Put icon
            top_margin = starting_top + (index_icon * size)
            await self._paste_image(
                stats_icon,
                (left_start, top_margin),
                stats_icon,
            )

            # Add stats name
            await self._write_text(
                stats_info.name,
                (left_start + size + 4, top_margin + (size // 2) + 2),
                20,
                anchor="lm",
                align="left",
            )
            is_percentage = stats_field not in non_percentage
            stats_format = "{:.1%}" if is_percentage else "{:.0f}"
            await self._write_text(
                stats_format.format(stats_value),
                (right_start, top_margin + (size // 2) + 2),
                20,
                anchor="rm",
                align="right",
            )

            index_icon += 1

    async def _set_index_prop_stats_info(self) -> None:
        for _, fields in self._index_data.properties.items():
            self._stats_fields_to_props[fields.kind] = fields

    async def _create_placeholder_slot(
        self,
        position: int,
        left: int,
        box_size: int = 138,
        margin: int = 25,
        text: str = "No Relic",
    ) -> None:
        top_margin = position * (box_size + margin)
        await self._create_box(
            ((left, top_margin), (left + box_size, top_margin + box_size)),
            width=8,
            color=self._foreground,
        )
        unknown_img = await self._async_open(self._assets_folder / "icon/character/None.png")
        unknown_img = await self._resize_image(unknown_img, (96, 96))
        unknown_img = await self._tint_image(unknown_img, self._foreground)

        await self._paste_image(
            unknown_img,
            (left + 21, top_margin + 21),
            unknown_img,
        )

        # Create another box on the right of the relic box
        await self._create_box(
            (
                (left + box_size + 25, top_margin + 5),
                (left + box_size + 25 + 254, top_margin + 4 + 26),
            ),
        )

        await self._write_text(
            text,
            (left + box_size + 25 + 4, top_margin + 4 + 6),
            color=self._background,
            anchor="lt",
            align="left",
        )

    async def _create_stats_box(
        self,
        position: int,
        left: int,
        main_stat: SRSCardStats,
        sub_stats: list[SRSCardStats],
        rarity: int,
        box_icon: str,
        box_indicator: str | None = None,
        score_indicator: str | None = None,
        box_size: int = 138,
        margin: int = 25,
        *,
        detailed: bool = False,
    ) -> None:
        top_margin = position * (box_size + margin)
        await self._create_box(
            ((left, top_margin), (left + box_size, top_margin + box_size)),
            width=8,
            color=self._foreground,
        )
        relic_img = await self._async_open(self._assets_folder / box_icon)
        relic_img = await self._resize_image(relic_img, (96, 96))

        await self._paste_image(
            relic_img,
            (left + 21, top_margin + 21),
            relic_img,
        )

        # Create another box on the right of the relic box
        await self._create_box(
            (
                (left + box_size + 25, top_margin + 5),
                (left + box_size + 25 + 254, top_margin + 4 + 26),
            ),
        )

        if box_indicator is not None:
            if len(box_indicator) > 3:
                raise ValueError(f"Invalid box indicator: {box_indicator}")
            # Create box at top-left of the relic box
            # There will be around 3 characters
            await self._create_box(
                (
                    (left + 4, top_margin + 4),
                    (left + 4 + 40, top_margin + 4 + 20),
                ),
            )
            await self._write_text(
                box_indicator,
                (left + 4 + 20, top_margin + 4 + 10),
                color=self._background,
                font_size=16,
                anchor="mm",
            )
        # Create box at top-right of the relic box for score indicator
        if score_indicator is not None:
            # Score indicator are 3 max, so make it smaller
            score_calc = await self._calc_text(score_indicator, 15)
            # Add 2px padding on the left and right
            await self._create_box(
                (
                    (left + box_size - 4 - score_calc - 12, top_margin + 4),
                    (left + box_size - 4, top_margin + 4 + 20),
                ),
            )
            # Center text
            await self._write_text(
                score_indicator,
                (left + box_size - 4 - score_calc - 4 + (score_calc // 2), top_margin + 4 + 10),
                color=self._background,
                font_size=15,
                anchor="mm",
            )

        # Main stats
        bbox_main_name = [left + box_size + 25 + 4, top_margin + 4 + 21]
        box_length = 254 if main_stat.value is None else 156
        bbox_main_name.append(left + box_size + 28 + box_length - 4)
        bbox_main_name.append(top_margin + 4 + 26)
        await self._write_text(
            main_stat.name,
            cast(tuple[int, int, int, int], tuple(bbox_main_name)),
            color=self._background,
            no_elipsis=not main_stat.cut_off,
            anchor="ls",
            align="left",
        )

        if main_stat.value is not None:
            stats_format = "{:.1%}" if main_stat.percent else "{:.0f}"
            await self._write_text(
                stats_format.format(main_stat.value),
                (left + box_size + 25 + 254 - 4, top_margin + 4 + 6),
                color=self._background,
                anchor="rt",
                align="right",
            )

        # Rarity icon
        stars_icon = await self._async_open(self._assets_folder / "icon" / "deco" / "StarBig_WhiteGlow.png")
        stars_icon = await self._tint_image(stars_icon, self._foreground)
        stars_icon = await self._resize_image(stars_icon, (14, 14))
        star_right_start = left + box_size - 14 - 8
        star_bottom_start = top_margin + box_size - 14 - 8
        for star_idx in range(rarity):
            await self._paste_image(
                stars_icon,
                (star_right_start - (star_idx * (14 - 2)), star_bottom_start),
                stars_icon,
            )

        # Substats
        for idx, sub_stat in enumerate(sub_stats, 1):
            if sub_stat.icon_url is not None:
                sub_stat_icon = await self._async_open(self._assets_folder / sub_stat.icon_url)
                # Tint icon
                sub_stat_icon = await self._tint_image(sub_stat_icon, self._foreground)
                # Resize icon
                sub_stat_icon = await self._resize_image(sub_stat_icon, (32, 32))

                await self._paste_image(
                    sub_stat_icon,
                    (
                        left + box_size + 20,
                        top_margin + 6 + (idx * 26),
                    ),
                    sub_stat_icon,
                )

                # Write the field name
                await self._write_text(
                    sub_stat.name,
                    (left + box_size + 20 + 32 + 2, top_margin + 16 + (idx * 26) + 13),
                    anchor="ls",
                    align="left",
                    font_size=16,
                )
            else:
                # Use name instead
                await self._write_text(
                    sub_stat.name,
                    (left + box_size + 24, top_margin + 8 + (idx * 26)),
                )

            if sub_stat.value is not None:
                stats_format = "{:.1%}" if sub_stat.percent else "{:.0f}"
                val_length = await self._write_text(
                    stats_format.format(sub_stat.value),
                    (
                        left + box_size + 25 + 254,
                        top_margin + 13 + (idx * 26),
                    ),
                    anchor="rt",
                    align="right",
                )
                # Roll count for detailed
                if detailed and sub_stat.count >= 0:
                    # The maximum possible roll count for each sub stat is:
                    # - Rarity 5: 4
                    # - Rarity 4: 3
                    # - Rarity 3: 2
                    # - Rarity 2: 1
                    # We want to adjust the alpha based on the roll count
                    # and the rarity. So each rarity will have different alpha scaling
                    # from 0.5 to 1.0
                    ALPHA_MAP = {
                        2: {1: 1.0},
                        3: {1: 0.5, 2: 1},
                        4: {1: 0.5, 2: 0.75, 3: 1},
                        5: {1: 0.5, 2: 0.67, 3: 0.84, 4: 1},
                    }
                    await self._write_text(
                        f"+{sub_stat.count} |",
                        (
                            left + box_size + 25 + 254 - val_length - 4,
                            top_margin + 22 + (idx * 26),
                        ),
                        font_size=12,
                        anchor="rm",
                        align="right",
                        alpha=round(ALPHA_MAP[rarity][sub_stat.count] * 255),
                    )

        # Close images
        await self._async_close(relic_img)

    async def _create_main_relics(self, relic_scores: RelicScores | None = None, *, detailed: bool = False) -> None:
        sorted_relics = sorted(
            self._character.relics,
            key=lambda r: self._index_data.relics[r.id].type.order,
        )
        # Group the relics by planar and non-planar
        main_relics: list[Relic] = []
        for relic in sorted_relics:
            relic_index = self._index_data.relics[relic.id]
            if relic_index.type in (SRSRelicType.PlanarOrb, SRSRelicType.PlanarRope):
                continue
            main_relics.append(relic)

        # If total main is != 4, create a placeholder
        for _ in range(4 - len(main_relics)):
            main_relics.append(
                Relic(
                    id="-1",
                    name="Unknown",
                    set_id="-1",
                    set_name="Unknown Set",
                    rarity=0,
                    icon_url="icon/character/None.png",
                    level=0,
                    main_stats=StatsProperties("None", StatsField.Unknown, "???", ""),
                    sub_stats=[],
                ),
            )

        relic_size = 138
        margin_relic = 25
        for idx, relic in enumerate(main_relics, 1):
            if relic.id == "-1":
                await self._create_placeholder_slot(
                    idx,
                    self.RELIC_LEFT,
                    relic_size,
                    margin_relic,
                    text=self._i18n.t("mihomo.no_relic"),
                )
            else:
                relic_score = relic_scores.scores.get(relic.id) if relic_scores is not None else None
                await self._create_stats_box(
                    position=idx,
                    left=self.RELIC_LEFT,
                    main_stat=SRSCardStats.from_relic(relic.main_stats, i18n=self._i18n),
                    sub_stats=[SRSCardStats.from_relic(sub, i18n=self._i18n) for sub in relic.sub_stats],
                    rarity=relic.rarity,
                    box_icon=relic.icon_url,
                    box_size=relic_size,
                    box_indicator=f"+{relic.level}",
                    score_indicator=relic_score.rank if relic_score is not None else None,
                    margin=margin_relic,
                    detailed=detailed,
                )

    async def _create_planar_and_light_cone(
        self, relic_scores: RelicScores | None = None, *, detailed: bool = False
    ) -> None:
        sorted_relics = sorted(
            self._character.relics,
            key=lambda r: self._index_data.relics[r.id].type.order,
        )
        # Group the relics by planar and non-planar
        planar_relics: list[Relic] = []
        for relic in sorted_relics:
            relic_index = self._index_data.relics[relic.id]
            if relic_index.type in (SRSRelicType.PlanarOrb, SRSRelicType.PlanarRope):
                planar_relics.append(relic)

        for _ in range(2 - len(planar_relics)):
            planar_relics.append(
                Relic(
                    id="-1",
                    name="Unknown",
                    set_id="-1",
                    set_name="Unknown Set",
                    rarity=0,
                    icon_url="icon/character/None.png",
                    level=0,
                    main_stats=StatsProperties("None", StatsField.Unknown, "???", ""),
                    sub_stats=[],
                ),
            )

        RELIC_LEFT = self.RELIC_LEFT + 138 + 28 + 254 + 60
        if self._character.light_cone is None:
            await self._create_placeholder_slot(1, RELIC_LEFT, text=self._i18n.t("mihomo.no_weapon"))
        else:
            light_cone = self._character.light_cone
            cone_stats = [SRSCardStats.from_relic(stats, i18n=self._i18n) for stats in light_cone.attributes]
            cone_stats.insert(
                0,
                SRSCardStats(
                    self._i18n.t("mihomo.level"),
                    value=light_cone.level,
                    cut_off=True,
                ),
            )
            lc_name = self._index_data.light_cones[light_cone.id].name
            await self._create_stats_box(
                position=1,
                left=RELIC_LEFT,
                main_stat=SRSCardStats(
                    name=lc_name,
                    cut_off=True,
                ),
                rarity=light_cone.rarity,
                sub_stats=cone_stats,
                box_icon=light_cone.icon_url,
                box_indicator=f"S{light_cone.superimpose}",
            )

        for idx, relic in enumerate(planar_relics, 2):
            if relic.id == "-1":
                await self._create_placeholder_slot(
                    idx,
                    RELIC_LEFT,
                    text=self._i18n.t("mihomo.no_relic"),
                )
            else:
                relic_score = relic_scores.scores.get(relic.id) if relic_scores is not None else None
                await self._create_stats_box(
                    position=idx,
                    left=RELIC_LEFT,
                    main_stat=SRSCardStats.from_relic(relic.main_stats, i18n=self._i18n),
                    sub_stats=[SRSCardStats.from_relic(sub, i18n=self._i18n) for sub in relic.sub_stats],
                    rarity=relic.rarity,
                    box_icon=relic.icon_url,
                    box_indicator=f"+{relic.level}",
                    score_indicator=relic_score.rank if relic_score is not None else None,
                    detailed=detailed,
                )

    async def _create_relic_sets_bonus(self) -> None:
        # Put after all the above relics
        TOP = 4 * (138 + 25) + 132 + 26
        MAX_HEIGHT = self._canvas.height - 30

        grouped_sets: dict[str, list[RelicSet]] = {}
        for relic_set in self._character.relic_sets:
            grouped_sets.setdefault(relic_set.id, []).append(relic_set)

        # Extend if has more than 2 sets
        extend_by = 0
        for relic_sets in grouped_sets.values():
            extend_by += 26 + 8
            select_relic = sorted(relic_sets, key=lambda r: r.need, reverse=True)[0]
            if select_relic.properties:
                extend_by += 26 + 2
        delta_extend = TOP + extend_by - MAX_HEIGHT
        if delta_extend > 0:
            await self._extend_canvas_down(delta_extend)

        for relic_sets in grouped_sets.values():
            select_relic = sorted(relic_sets, key=lambda r: r.need, reverse=True)[0]

            # Create 1:1 box for text
            await self._create_box(
                ((self.RELIC_LEFT, TOP), (self.RELIC_LEFT + 20, TOP + 20)),
            )
            await self._write_text(
                f"{select_relic.need}",
                (self.RELIC_LEFT + 10, TOP + 10.5),
                font_size=16,
                color=self._background,
                anchor="mm",
                align="center",
            )
            # Create the set name
            properties_joined = []
            for prop in select_relic.properties:
                prop_info = self._index_data.properties[prop.type]
                prop_fmt = "{:.1%}" if prop.percent else "{:.0f}"
                properties_joined.append(f"{prop_info.name} {prop_fmt.format(prop.value)}")
            relic_set_name = self._index_data.relics_sets[select_relic.id].name
            await self._write_text(
                relic_set_name,
                (self.RELIC_LEFT + 21 + 8, TOP + 10.5),
                font_size=16,
                anchor="lm",
                align="left",
            )
            if properties_joined:
                # Create after the set name
                await self._write_text(
                    "(" + ", ".join(properties_joined) + ")",
                    (self.RELIC_LEFT + 21 + 8, TOP + 10.5 + 26),
                    font_size=16,
                    anchor="lm",
                    align="left",
                )
                TOP += 26
            TOP += 26

    async def _create_eidolons(self) -> None:
        MARGIN_TOP = 670
        ICON_SIZE = 65
        MARGIN_LEFT = self.RELIC_LEFT + 138 + 28 + 254 + 60
        ICON_MARGIN = 6

        if self._character.eidolon == 0:
            # We do not need to create eidolons icons because of waste of space.
            return

        eidolon_len = await self._calc_text(self._i18n.t("mihomo.eidolons"), font_size=18)

        DEMARGIN = 28

        await self._create_box(
            ((MARGIN_LEFT, MARGIN_TOP - DEMARGIN - 1), (MARGIN_LEFT + eidolon_len + 10, MARGIN_TOP - DEMARGIN + 21)),
        )
        await self._write_text(
            self._i18n.t("mihomo.eidolons"),
            (MARGIN_LEFT + 5, MARGIN_TOP - DEMARGIN + 17),
            font_size=18,
            color=self._background,
            anchor="ls",
            align="left",
        )

        character_info = self._index_data.characters[self._character.id]
        eidolons_data = [self._index_data.characters_eidolons[eidolon_id] for eidolon_id in character_info.eidolon_ids]
        eidolons_data.sort(key=lambda e: e.rank)

        for idx, eidolon in enumerate(eidolons_data):
            active = eidolon.rank <= self._character.eidolon

            eidolon_icon = await self._async_open(self._assets_folder / eidolon.icon_url)
            eidolon_icon = await self._tint_image(eidolon_icon, self._foreground)
            if not active:
                await self._set_transparency_fast(eidolon_icon, 0.5)
            eidolon_icon = await self._resize_image(eidolon_icon, (ICON_SIZE, ICON_SIZE))

            await self._paste_image(
                eidolon_icon,
                (MARGIN_LEFT + ((eidolon_icon.width + ICON_MARGIN) * idx), MARGIN_TOP),
                eidolon_icon,
            )
            await self._async_close(eidolon_icon)

    async def _create_skills_and_traces(self) -> None:
        sorted_skills = sorted(
            self._character.skills,
            key=lambda r: r.type.order,
        )
        # Remove the skill of MazeAttack
        sorted_skills = [skill for skill in sorted_skills if skill.type != SkillUsageType.TechniqueAttack]
        # Remove duplicates skill
        sorted_skills = list({skill.type: skill for skill in sorted_skills}.values())
        ADD_MARGIN = 65 + 40

        # We want to autoscale the skills to fit the boundary
        LEFT = 552
        TOP = 658
        if self._character.eidolon > 0:
            TOP += ADD_MARGIN

            EXTEND_BY = 55
            delta_extend = EXTEND_BY - self._extend_down_by
            if delta_extend > 0:
                await self._extend_canvas_down(delta_extend)
            line_left = self.RELIC_LEFT + 138 + 28 + 254 + 60
            line_right = line_left + (65 + 5) * 6
            await self._create_line(
                (line_left - 2, TOP - 18, line_right - 2, TOP - 18),
                width=2,
            )
        SIZE_W = 448

        # Check margin and 1:1 ratio of image size that we need to use
        box_size = 84
        margin = SIZE_W - (box_size * len(sorted_skills)) + (box_size // 2) + 8

        for idx, skill in enumerate(sorted_skills):
            skill_icon = await self._async_open(self._assets_folder / skill.icon_url)
            skill_icon = await self._tint_image(skill_icon, self._foreground)
            skill_alpha = 1
            if skill.type == SkillUsageType.Technique and skill.level == 0:
                skill_alpha = 0.5
                await self._set_transparency_fast(skill_icon, skill_alpha)
            skill_icon = await self._resize_image(skill_icon, (box_size - 4, box_size - 4))

            # Skill icon
            await self._paste_image(
                skill_icon,
                (LEFT + (idx * margin) + 2, TOP),
                skill_icon,
            )
            # Skill level
            if skill.type != SkillUsageType.Technique:
                value_skill = f"{skill.level:02d}"
                await self._create_box(
                    ((LEFT + (idx * margin) + 2, TOP), (LEFT + (idx * margin) + 36, TOP + 20)),
                )
                await self._write_text(
                    value_skill,
                    (LEFT + (idx * margin) + 19, TOP + 11),
                    font_size=16,
                    anchor="mm",
                    color=self._background,
                )

            match skill.type:
                case SkillUsageType.Basic:
                    skill_typet = self._i18n.t("mihomo.basic_atk")
                case SkillUsageType.Skill:
                    skill_typet = self._i18n.t("mihomo.skill")
                case SkillUsageType.Ultimate:
                    skill_typet = self._i18n.t("mihomo.ultimate")
                case SkillUsageType.Talent:
                    skill_typet = self._i18n.t("mihomo.talent")
                case SkillUsageType.Technique:
                    skill_typet = self._i18n.t("mihomo.technique")
                case SkillUsageType.TechniqueAttack:
                    skill_typet = self._i18n.t("mihomo.technique")
                case _:
                    skill_typet = skill.type_description

            await self._write_text(
                skill_typet,
                (LEFT + (idx * margin) + 2 + (skill_icon.width // 2), TOP + skill_icon.height + 8),
                font_size=14,
                anchor="mm",
                alpha=round(skill_alpha * 255),
            )

            # Close image
            await self._async_close(skill_icon)

        major_traces: list[SkillTrace] = []
        for trace in self._character.traces:
            if "skilltree" in trace.icon_url:
                major_traces.append(trace)

        # We want to autoscale the skills to fit the boundary
        LEFT = 648
        TOP = 760
        if self._character.eidolon > 0:
            TOP += ADD_MARGIN
        SIZE_W = 200

        # Check margin and 1:1 ratio of image size that we need to use
        box_size = 48
        margin = 78

        major_traces.sort(key=lambda t: t.icon_url)

        for idx, trace in enumerate(major_traces):
            trace_icon = await self._async_open(self._assets_folder / trace.icon_url)
            trace_icon = await self._tint_image(trace_icon, self._foreground)
            trace_alpha = 1
            if trace.level < 1:
                trace_alpha = 0.5
                await self._set_transparency_fast(trace_icon, trace_alpha)
            trace_icon = await self._resize_image(trace_icon, (box_size - 4, box_size - 4))

            await self._paste_image(
                trace_icon,
                (LEFT + (idx * margin) + 2, TOP),
                trace_icon,
            )

            await self._write_text(
                f"A{(idx + 1) * 2}",
                (LEFT + (idx * margin) + 2 + (trace_icon.width // 2), TOP + trace_icon.height + 10),
                font_size=13,
                anchor="mm",
                alpha=round(trace_alpha * 255),
            )

            # Close image
            await self._async_close(trace_icon)

    async def create(self, *, hide_uid: bool = False, hide_credits: bool = False, detailed: bool = False) -> bytes:
        self._assets_folder = await self._assets_folder.absolute()
        if not await self._assets_folder.exists():
            raise FileNotFoundError("The assets folder does not exist.")
        await self._index_data.async_loads()
        await self._relic_scorer.async_load()
        await self._set_index_prop_stats_info()

        t = self._i18n.t

        # Calculate average color of the preview image.
        self.logger.info("Initializing the canvas card information...")
        dominant_and_inversion = _COLOR_DOMINANT.get(self._character.id)
        if dominant_and_inversion is None:
            raise ValueError("The dominant color of the character is missing.")

        # Set the background color to dominant color.
        if isinstance(dominant_and_inversion, list):
            await self._paste_image(dominant_and_inversion[0], (0, 0, self._canvas.width, self._canvas.height))
            self._foreground = dominant_and_inversion[1]
            self._background = dominant_and_inversion[0]
        else:
            await self._paste_image(dominant_and_inversion, (0, 0, self._canvas.width, self._canvas.height))
            self._foreground = cast(RGB, tuple(255 - c for c in dominant_and_inversion))
            self._background = dominant_and_inversion

        self.logger.info("Adding player name...")
        middle_bbox_name = self.CHARACTER_TOP // 2
        await self._write_text(
            self._player.name,
            (self.RELIC_LEFT + 140, self.CHARACTER_TOP - middle_bbox_name),
            font_size=72,
            anchor="lm",
        )
        # Player avatar
        avatar_icon = await self._async_open(self._assets_folder / self._player.avatar.icon_url)
        avatar_icon = await self._resize_image(avatar_icon, (120, 120))
        await self._paste_image(
            avatar_icon,
            (self.RELIC_LEFT, self.CHARACTER_TOP - 144),
            avatar_icon,
        )
        await self._create_circle(
            [self.RELIC_LEFT, self.CHARACTER_TOP - 144, self.RELIC_LEFT + 120, self.CHARACTER_TOP - 144 + 120],
            4,
            self._foreground,
            8,
        )
        await self._async_close(avatar_icon)

        # Create the character card header.
        self.logger.info("Creating the character card header...")
        await self._create_character_card_header()
        self.logger.info("Creating the character card stats...")
        await self._create_character_stats()

        # Create relics sets
        try:
            self.logger.info("Trying to get relic scores...")
            relic_scores = self._relic_scorer.calculate(self._character, loader=self._index_data)
        except RelicScoringNoSuchCharacterException:
            relic_scores = None
        self.logger.info("Creating the character relics...")
        await self._create_main_relics(relic_scores=relic_scores, detailed=detailed)
        self.logger.info("Creating the character planar and light cone...")
        await self._create_planar_and_light_cone(relic_scores=relic_scores, detailed=detailed)
        self.logger.info("Creating relic set bonus...")
        await self._create_relic_sets_bonus()

        # Create eidolons
        self.logger.info("Creating the character eidolons...")
        await self._create_eidolons()

        # Create skills
        self.logger.info("Creating the character skills...")
        await self._create_skills_and_traces()

        # Create footer
        self.logger.info("Creating the character footer...")
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
                t("mihomo.credits"),
                (self._canvas.width - 20, self._canvas.height - 20),
                font_size=20,
                alpha=128,
                anchor="rs",
            )

        # Outer canvas
        main_canvas = Image.new("RGBA", (1600, self._canvas.height + 90), self._foreground)
        # 16px padding left, right, top on where to paste the old canvas
        await self._paste_image(self._canvas, (16, 16), self._canvas, canvas=main_canvas)
        player_region = HYVServer.from_uid(self._player.id, ignore_error=True)
        starting_foot = self._canvas.height
        height_mid = starting_foot + ((main_canvas.height - starting_foot) // 2) + 8
        player_uid = f"UID: {self._player.id}"
        if player_region is not None:
            player_reg_name = _get_player_server(player_region, self._i18n.t)
            player_uid += f" | {t('mihomo.region')}: {player_reg_name}"
        player_uid += f" | {t('mihomo.level')}: {self._player.level:02d}"
        if hide_uid:
            player_uid = f"{t('mihomo.level')}: {self._player.level:02d}"
        await self._write_text(
            player_uid,
            (75, height_mid),
            font_size=30,
            color=self._background,
            anchor="lm",
            canvas=main_canvas,
        )
        right_side_text = f"{t('chronicles.achievements')}: {self._player.progression.achivements}"
        if self._player.progression.forgotten_hall is not None:
            forgotten_hall = self._player.progression.forgotten_hall
            if forgotten_hall.moc_finished_floor > 0:
                moc_floor = t("moc_floor", [str(forgotten_hall.moc_finished_floor)])
                right_side_text = f"{t('mihomo.moc')}: {moc_floor} | {right_side_text}"
        await self._write_text(
            right_side_text,
            (main_canvas.width - 75, height_mid),
            font_size=30,
            color=self._background,
            anchor="rm",
            canvas=main_canvas,
        )

        # Save the image.
        self.logger.info("Saving the image...")
        bytes_io = await self._async_save_bytes(main_canvas)

        self.logger.info("Cleaning up...")
        await self._async_close(main_canvas)
        await self._async_close(self._canvas)
        await self.close()

        # Return the bytes.
        bytes_io.seek(0)
        all_bytes = await self._loop.run_in_executor(None, bytes_io.read)
        bytes_io.close()
        return all_bytes
