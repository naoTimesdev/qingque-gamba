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
import functools
import logging
from enum import Enum
from io import BytesIO
from typing import Any, TypeAlias

import msgspec
import orjson
from aiopath import AsyncPath
from msgspec import field
from PIL import Image, ImageDraw, ImageFont, ImageOps

from qingque.mihomo.models.base import MihomoBase
from qingque.mihomo.models.characters import Character
from qingque.mihomo.models.combats import ElementType, SkillTrace, SkillUsageType
from qingque.mihomo.models.constants import MihomoLanguage
from qingque.mihomo.models.helper import get_actual_moc_floor, get_uid_region
from qingque.mihomo.models.player import PlayerInfo
from qingque.mihomo.models.relics import Relic, RelicSet
from qingque.mihomo.models.stats import StatsAtrributes, StatsField, StatsProperties

__all__ = (
    "SRSRelicType",
    "SRSRelic",
    "SRSCardStats",
    "StarRailCard",
)
RGB: TypeAlias = tuple[int, int, int]

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
    "1109": (223, 176, 109),
    "1110": (34, 83, 172),
    "1111": [(130, 25, 45), (220, 206, 199)],
    "1201": (55, 86, 93),
    "1202": [(239, 211, 148), (206, 60, 49)],
    "1203": (81, 99, 93),
    "1204": (201, 186, 170),
    "1205": (69, 52, 62),
    "1206": (204, 200, 188),
    "1207": [(144, 163, 152), (55, 86, 93)],
    "1208": [(77, 54, 91), (230, 131, 204)],
    "1209": (49, 109, 173),
    "1211": [(75, 102, 163), (205, 176, 219)],
    "1213": [(34, 42, 46), (94, 255, 255)],
    "8001": (48, 44, 62),
    "8002": (48, 44, 62),
    "8003": (192, 165, 148),
    "8004": (194, 165, 148),
}
logger = logging.getLogger("qingque.starrail.card_generator")


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


def draw_ellipse(
    image: Image.Image,
    bounds: list[int],
    width: int = 1,
    outline: str | RGB = "white",
    antialias: int = 4,
):
    """Improved ellipse drawing function, based on PIL.ImageDraw.

    Source: https://stackoverflow.com/a/34926008
    """

    # Use a single channel image (mode='L') as mask.
    # The size of the mask can be increased relative to the imput image
    # to get smoother looking results.
    mask = Image.new(size=[int(dim * antialias) for dim in image.size], mode="L", color="black")  # type: ignore
    draw = ImageDraw.Draw(mask)

    # draw outer shape in white (color) and inner shape in black (transparent)
    for offset, fill in (width / -2.0, "white"), (width / 2.0, "black"):
        left, top = [(value + offset) * antialias for value in bounds[:2]]
        right, bottom = [(value - offset) * antialias for value in bounds[2:]]
        draw.ellipse([left, top, right, bottom], fill=fill)

    # downsample the mask using PIL.Image.LANCZOS
    # (a high-quality downsampling filter).
    mask = mask.resize(image.size, Image.LANCZOS)
    # paste outline color to input image through the mask
    image.paste(outline, mask=mask)


class SRSRelicType(str, Enum):
    Head = "HEAD"
    Hand = "HAND"
    Body = "BODY"
    Foot = "FOOT"
    PlanarOrb = "NECK"
    PlanarRope = "OBJECT"

    @property
    def order(self) -> int:
        return {
            SRSRelicType.Head: 1,
            SRSRelicType.Hand: 2,
            SRSRelicType.Body: 3,
            SRSRelicType.Foot: 4,
            SRSRelicType.PlanarOrb: 5,
            SRSRelicType.PlanarRope: 6,
        }[self]


class SRSRelic(MihomoBase, frozen=True):
    id: str
    set_id: str
    name: str
    rarity: int
    type: SRSRelicType
    icon_url: str = field(name="icon")


class SRSCardStats(MihomoBase, frozen=True):
    name: str
    icon_url: str | None = None
    value: int | float | None = None
    percent: bool = False
    cut_off: bool = False

    @classmethod
    def from_relic(cls: type[SRSCardStats], relic: StatsProperties | StatsAtrributes, cut_off: bool = False):
        return cls(
            name=relic.field.simple,
            icon_url=relic.icon_url,
            value=relic.value,
            percent=relic.percent,
            cut_off=cut_off,
        )


class StarRailCard:
    CHARACTER_TOP = 164
    CHARACTER_BOTTOM = CHARACTER_TOP + 352
    CHARACTER_LEFT = 1006
    CHARACTER_RIGHT = CHARACTER_LEFT + 500

    RELIC_LEFT = 62

    def __init__(
        self, character: Character, player: PlayerInfo, *, language: MihomoLanguage = MihomoLanguage.EN
    ) -> None:
        self._player: PlayerInfo = player
        self._character: Character = character
        self._language: MihomoLanguage = language
        self._loop = asyncio.get_running_loop()

        # Initialize the card canvas.
        # Inner canvas is 1568x910
        self._canvas = Image.new("RGBA", (1568, 910), (255, 255, 255))
        self._assets_folder = AsyncPath(__file__).parent.parent / "assets" / "srs"
        self._index_folder = self._assets_folder / "index" / f"{self._language.value}"

        self._foreground: RGB = (255, 255, 255)
        self._background: RGB = (0, 0, 0)
        self._font_path: AsyncPath = self._assets_folder / ".." / "fonts" / "SDK_SC_Web.ttf"
        self._universe_font_path: AsyncPath = self._assets_folder / ".." / "fonts" / "FirstWorld.ttf"

        self._stats_field_to_name: dict[StatsField, str] = {}
        self._relics: dict[str, SRSRelic] = {}

        self._extended_by: int = 0

    def is_trailblazer(self):
        return int(self._character.id) >= 8001

    async def _async_open(self, img_path: AsyncPath) -> Image.Image:
        io = BytesIO()
        read_data = await img_path.read_bytes()
        io.write(read_data)
        io.seek(0)
        # Open as RGBA in case the image is transparent.
        as_image = (await self._loop.run_in_executor(None, Image.open, io)).convert("RGBA")
        return as_image

    async def _create_font(self, font_path: AsyncPath, size: int = 20):
        font = await self._loop.run_in_executor(None, ImageFont.truetype, str(font_path), size)
        return font

    async def _get_draw(self, *, canvas: Image.Image | None = None):
        canvas = canvas or self._canvas
        return await self._loop.run_in_executor(None, ImageDraw.Draw, canvas)

    async def _extend_canvas_down(self, height: int):
        new_canvas = Image.new("RGBA", (self._canvas.width, self._canvas.height + height), (255, 255, 255))
        # Paste background
        # self._canvas.paste(dominant_and_inversion, (0, 0, self._canvas.width, self._canvas.height))
        await self._loop.run_in_executor(
            None, new_canvas.paste, self._background, (0, 0, new_canvas.width, new_canvas.height)
        )
        await self._loop.run_in_executor(None, new_canvas.paste, self._canvas, (0, 0), self._canvas)
        self._canvas = new_canvas
        self._extended_by += height

    async def _write_text(
        self,
        content: str,
        box: tuple[float, float] | tuple[float, float, float, float],
        font_size: int = 20,
        font_path: AsyncPath | None = None,
        use_bg: bool = False,
        no_elipsis: bool = False,
        alpha: int = 255,
        *,
        canvas: Image.Image | None = None,
        **kwargs: Any,
    ):
        kwargs.pop("fill", None)
        kwargs.pop("font", None)
        kwargs.pop("xy", None)
        kwargs.pop("text", None)
        canvas = canvas or self._canvas

        if len(box) != 2 and len(box) != 4:
            raise ValueError(f"Invalid box size: {box}")

        right = -1
        if len(box) == 4:
            # Pop the last two
            right, _ = box[2:]  # type: ignore
            box = box[:2]

        font_path = font_path or self._font_path
        font = await self._create_font(font_path, font_size)
        composite: Image.Image | None = None
        if alpha < 255:
            composite = Image.new("RGBA", self._canvas.size, (255, 255, 255, 0))
            draw = await self._get_draw(canvas=composite)
        else:
            draw = await self._get_draw(canvas=canvas)

        if right != -1:
            box_width = right - box[0]
            # We want to ensure the text fit the box.
            # Use textlength to determine how much we need to cut off the text with ...

            original_content = content
            # Get the text length
            text_width = await self._loop.run_in_executor(None, draw.textlength, content, font)
            while text_width > box_width:
                # Cut off content + ...
                content = content[:-1]
                if not content:
                    break
                tst_content = content + " ..." if not no_elipsis else content
                text_width = await self._loop.run_in_executor(None, draw.textlength, tst_content, font)
            if not no_elipsis and original_content != content:
                content += " ..."

        fill = self._background if use_bg else self._foreground
        draw_text = functools.partial(draw.text, fill=(*fill, alpha), font=font, **kwargs)
        await self._loop.run_in_executor(None, draw_text, box, content)
        length_width = await self._loop.run_in_executor(None, draw.textlength, content, font)
        if composite is not None:
            await self._loop.run_in_executor(None, canvas.alpha_composite, composite)
        return length_width

    async def _create_box(
        self, box: tuple[tuple[float, float], tuple[float, float]], use_bg: bool = False, width: int = 0
    ):
        draw = await self._get_draw()
        fill = self._background if use_bg else self._foreground
        outline = None
        if width > 0:
            outline = self._foreground if use_bg else self._background
            fill = None
        draw_rect = functools.partial(draw.rectangle, fill=fill, width=width, outline=outline)
        await self._loop.run_in_executor(None, draw_rect, box)

    async def _tint_image(self, im: Image.Image, color: RGB):
        alpha = im.split()[3]
        gray = await self._loop.run_in_executor(None, ImageOps.grayscale, im)
        result = await self._loop.run_in_executor(None, ImageOps.colorize, gray, color, color)
        await self._loop.run_in_executor(None, result.putalpha, alpha)
        return result

    def _get_element(self, element: ElementType):
        elem_txt = element.name
        if elem_txt == "Thunder":
            elem_txt = "Lightning"
        element_path = self._assets_folder / "icon" / "element" / f"{elem_txt}White.png"
        return element_path

    async def _create_character_card_header(self):
        # Load the character preview image.
        preview_path = self._assets_folder / self._character.preview_url
        preview_image = await self._async_open(preview_path)

        # Write the character name.
        chara_name = self._character.name
        if "{NICKNAME}" in chara_name:
            chara_name = chara_name.replace("{NICKNAME}", f"Trailblazer ({self._player.name})")
        if self.is_trailblazer() and "{NICKNAME}" not in chara_name:
            chara_name = f"Trailblazer ({chara_name})"
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
        preview_image = await self._loop.run_in_executor(
            None,
            preview_image.crop,
            (0, _pr_top_crop, preview_image.width, preview_image.height - _pr_bot_crop),
        )

        # Start: 1006, 184
        # End: 1506, 536
        # Using the above number, create a rectangle with foreground color.
        await self._create_box(
            ((self.CHARACTER_LEFT, self.CHARACTER_TOP), (self.CHARACTER_RIGHT, self.CHARACTER_BOTTOM)),
        )

        # Put the preview image on the canvas, shift by 4px to the right and bottom.
        await self._loop.run_in_executor(
            None,
            self._canvas.paste,
            preview_image,
            (self.CHARACTER_LEFT + 4, self.CHARACTER_TOP + 4),
            preview_image,
        )

        # Write the Level text
        # Pad: 14px, y: center between image and bottom
        await self._write_text(
            "Level",
            (self.CHARACTER_LEFT + 14, self.CHARACTER_BOTTOM - 22),
            font_size=24,
            use_bg=True,
            anchor="lm",
            align="left",
        )

        # Write the Level number
        await self._write_text(
            str(self._character.level).zfill(2),
            (self.CHARACTER_RIGHT - 14, self.CHARACTER_BOTTOM - 22),
            font_size=24,
            use_bg=True,
            anchor="rm",
            align="right",
        )

        # Starting in top-left of the rectangle, we want to write the character eidolons level
        await self._create_box(
            (
                (self.CHARACTER_LEFT, self.CHARACTER_TOP),
                (self.CHARACTER_LEFT + 40, self.CHARACTER_TOP + 32),
            ),
        )
        await self._write_text(
            f"E{self._character.eidolon}",
            (self.CHARACTER_LEFT + 8, self.CHARACTER_TOP + 8),
            font_size=19,
            use_bg=True,
            anchor="lt",
            align="left",
        )

        element_img = await self._async_open(self._get_element(self._character.element.id))
        element_img = await self._tint_image(element_img, self._background)
        # Resize
        element_img = await self._loop.run_in_executor(None, element_img.resize, (96, 96))
        await self._loop.run_in_executor(
            None,
            self._canvas.paste,
            element_img,
            (self.CHARACTER_RIGHT - 108, self.CHARACTER_TOP + 64),
            element_img,
        )

        # Write the character trailblaze path
        path_img = await self._async_open(self._assets_folder / self._character.path.icon_url)
        path_img = await self._tint_image(path_img, self._background)
        # Resize
        path_img = await self._loop.run_in_executor(None, path_img.resize, (96, 96))
        await self._loop.run_in_executor(
            None,
            self._canvas.paste,
            path_img,
            (self.CHARACTER_RIGHT - 108, self.CHARACTER_TOP + 176),
            path_img,
        )

        # Write text at top-right of the rectangle for Element / Path
        elem_path_width = await self._write_text(
            f"{self._character.element.name} / {self._character.path.name}",
            (self.CHARACTER_RIGHT - 4, self.CHARACTER_TOP + 8),
            font_size=20,
            use_bg=True,
            anchor="rt",
            align="right",
        )
        # Create a box for the text
        await self._create_box(
            (
                (self.CHARACTER_RIGHT - elem_path_width - 8, self.CHARACTER_TOP),
                (self.CHARACTER_RIGHT, self.CHARACTER_TOP + 32),
            ),
        )
        await self._write_text(
            f"{self._character.element.name} / {self._character.path.name}",
            (self.CHARACTER_RIGHT - 4, self.CHARACTER_TOP + 8),
            font_size=20,
            use_bg=True,
            anchor="rt",
            align="right",
        )

        # Put the rarity stars
        stars_icon = await self._async_open(self._assets_folder / "icon" / "deco" / "StarBig_WhiteGlow.png")
        stars_icon = await self._tint_image(stars_icon, self._background)
        stars_icon = await self._loop.run_in_executor(None, stars_icon.resize, (24, 24))
        star_right_start = self.CHARACTER_RIGHT - 24 - 4
        top_marg_star = self.CHARACTER_TOP + 20 + 12
        for idx in range(self._character.rarity):
            # Every 24px, we want to put the star from right to left.
            await self._loop.run_in_executor(
                None,
                self._canvas.paste,
                stars_icon,
                (star_right_start - (idx * 24), top_marg_star),
                stars_icon,
            )

    async def _combine_character_stats(self):
        stats_meta: dict[StatsField, int | float] = {
            StatsField.HP: 1,
            StatsField.ATK: 1,
            StatsField.DEF: 1,
            StatsField.Speed: 1,
            StatsField.CritRate: 0.0,
            StatsField.CritDamage: 0.0,
            StatsField.BreakEffect: 0.0,
            StatsField.HealingRate: 0.0,
            StatsField.EnergyRegenRate: 0.0,
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
        percentage_stats: dict[StatsField, int | float] = {}
        icon_sets: dict[StatsField, Image.Image] = {}
        # Do the stats calculation here.
        for stats in self._character.attributes:
            stats_meta[stats.field] += stats.value
            percentage_stats[stats.field] = stats.percent
            has_icon = icon_sets.get(stats.field)
            if not has_icon:
                icon_sets[stats.field] = await self._async_open(self._assets_folder / stats.icon_url)
        for stats in self._character.additions:
            stats_meta[stats.field] += stats.value
            percentage_stats[stats.field] = stats.percent
            has_icon = icon_sets.get(stats.field)
            if not has_icon:
                icon_sets[stats.field] = await self._async_open(self._assets_folder / stats.icon_url)
        return stats_meta, percentage_stats, icon_sets

    async def _create_character_stats(self):
        size = 32
        starting_top = self.CHARACTER_BOTTOM - 22
        left_start = 1006
        right_start = 1506
        index_icon = 1
        stats_meta, percentage_stats, icon_sets = await self._combine_character_stats()
        valid_meta_entries = {k: v for k, v in stats_meta.items() if v > 0.0}
        # Check if it's more than 10 entries, if it's extend the canvas.
        if len(valid_meta_entries) > 10:
            await self._extend_canvas_down((len(valid_meta_entries) - 10) * (size + 2))
        for stats_field, stats_value in valid_meta_entries.items():
            if stats_value <= 0.0:
                continue
            percentage_mode = percentage_stats.get(stats_field, False)
            img_icon = icon_sets.get(stats_field)
            if img_icon is None:
                raise ValueError(f"Cannot find icon for {stats_field.name}")

            # Tint icon
            tinted_icon = await self._tint_image(img_icon, self._foreground)
            # Resize icon
            tinted_icon = await self._loop.run_in_executor(None, tinted_icon.resize, (size, size))

            # Put icon
            top_margin = starting_top + (index_icon * size)
            await self._loop.run_in_executor(
                None,
                self._canvas.paste,
                tinted_icon,
                (left_start, top_margin),
                tinted_icon,
            )

            # Add text
            stats_name = self._stats_field_to_name.get(stats_field)
            if stats_name is None:
                raise ValueError(f"Cannot find stats name for {stats_field.name}")
            await self._write_text(
                stats_name,
                (left_start + size + 10, top_margin + (size // 2) + 2),
                20,
                anchor="lm",
                align="left",
            )
            stats_format = "{:.1%}" if percentage_mode else "{:.0f}"
            await self._write_text(
                stats_format.format(stats_value),
                (right_start, top_margin + (size // 2) + 2),
                20,
                anchor="rm",
                align="right",
            )

            index_icon += 1

    async def _set_index_properties_name(self):
        properties_json = orjson.loads(await (self._index_folder / "properties.json").read_bytes())
        for _, fields in properties_json.items():
            field_name = StatsField(fields["field"])
            self._stats_field_to_name[field_name] = fields["name"]

    async def _set_index_relics(self):
        relics_json = orjson.loads(await (self._index_folder / "relics.json").read_bytes())
        for relic in relics_json.values():
            self._relics[relic["id"]] = msgspec.json.decode(orjson.dumps(relic), type=SRSRelic)

    async def _create_placeholder_slot(
        self,
        position: int,
        left: int,
        box_size: int = 138,
        margin: int = 25,
        text: str = "No Relic",
    ):
        top_margin = position * (box_size + margin)
        await self._create_box(
            ((left, top_margin), (left + box_size, top_margin + box_size)),
            width=8,
            use_bg=True,
        )
        relic_img = await self._async_open(self._assets_folder / "icon/character/None.png")
        relic_img = await self._loop.run_in_executor(None, relic_img.resize, (96, 96))
        relic_img = await self._tint_image(relic_img, self._foreground)

        await self._loop.run_in_executor(
            None,
            self._canvas.paste,
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

        await self._write_text(
            text,
            (left + box_size + 25 + 4, top_margin + 4 + 6),
            use_bg=True,
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
        box_size: int = 138,
        margin: int = 25,
    ):
        top_margin = position * (box_size + margin)
        await self._create_box(
            ((left, top_margin), (left + box_size, top_margin + box_size)),
            width=8,
            use_bg=True,
        )
        relic_img = await self._async_open(self._assets_folder / box_icon)
        relic_img = await self._loop.run_in_executor(None, relic_img.resize, (96, 96))

        await self._loop.run_in_executor(
            None,
            self._canvas.paste,
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
                use_bg=True,
                font_size=16,
                anchor="mm",
            )

        # Main stats
        bbox_main_name = [left + box_size + 25 + 4, top_margin + 4 + 6]
        box_length = 254 if main_stat.value is None else 156
        bbox_main_name.append(left + box_size + 28 + box_length - 4)
        bbox_main_name.append(top_margin + 4 + 26)
        await self._write_text(
            main_stat.name,
            tuple(bbox_main_name),
            use_bg=True,
            no_elipsis=not main_stat.cut_off,
            anchor="lt",
            align="left",
        )

        if main_stat.value is not None:
            stats_format = "{:.1%}" if main_stat.percent else "{:.0f}"
            await self._write_text(
                stats_format.format(main_stat.value),
                (left + box_size + 25 + 254 - 4, top_margin + 4 + 6),
                use_bg=True,
                anchor="rt",
                align="right",
            )

        stars_icon = await self._async_open(self._assets_folder / "icon" / "deco" / "StarBig_WhiteGlow.png")
        stars_icon = await self._tint_image(stars_icon, self._foreground)
        stars_icon = await self._loop.run_in_executor(None, stars_icon.resize, (14, 14))
        star_right_start = left + box_size - 14 - 8
        star_bottom_start = top_margin + box_size - 14 - 8
        for star_idx in range(rarity):
            await self._loop.run_in_executor(
                None,
                self._canvas.paste,
                stars_icon,
                (star_right_start - (star_idx * (14 - 2)), star_bottom_start),
                stars_icon,
            )

        for idx, sub_stat in enumerate(sub_stats, 1):
            if sub_stat.icon_url is not None:
                relic_icon = await self._async_open(self._assets_folder / sub_stat.icon_url)
                # Tint icon
                relic_icon = await self._tint_image(relic_icon, self._foreground)
                # Resize icon
                relic_icon = await self._loop.run_in_executor(None, relic_icon.resize, (32, 32))

                await self._loop.run_in_executor(
                    None,
                    self._canvas.paste,
                    relic_icon,
                    (
                        left + box_size + 20,
                        top_margin + 6 + (idx * 26),
                    ),
                    relic_icon,
                )

                # Write the field name
                sub_stat_name = sub_stat.name
                if sub_stat.percent:
                    sub_stat_name = f"{sub_stat_name}%"
                await self._write_text(
                    sub_stat_name,
                    (left + box_size + 20 + 32 + 4, top_margin + 16 + (idx * 26)),
                    anchor="lt",
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
                await self._write_text(
                    stats_format.format(sub_stat.value),
                    (
                        left + box_size + 25 + 254,
                        top_margin + 13 + (idx * 26),
                    ),
                    anchor="rt",
                    align="right",
                )

    async def _create_main_relics(self):
        sorted_relics = sorted(
            self._character.relics,
            key=lambda r: self._relics[r.id].type.order,
        )
        # Group the relics by planar and non-planar
        main_relics: list[Relic] = []
        for relic in sorted_relics:
            relic_index = self._relics[relic.id]
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
                await self._create_placeholder_slot(idx, self.RELIC_LEFT, relic_size, margin_relic)
            else:
                await self._create_stats_box(
                    position=idx,
                    left=self.RELIC_LEFT,
                    main_stat=SRSCardStats.from_relic(relic.main_stats),
                    sub_stats=[SRSCardStats.from_relic(sub) for sub in relic.sub_stats],
                    rarity=relic.rarity,
                    box_icon=relic.icon_url,
                    box_size=relic_size,
                    box_indicator=f"+{relic.level}",
                    margin=margin_relic,
                )

    async def _create_relic_sets_bonus(self):
        # Put after all the above relics
        TOP = 4 * (138 + 25) + 132

        grouped_sets: dict[str, list[RelicSet]] = {}
        for relic_set in self._character.relic_sets:
            grouped_sets.setdefault(relic_set.id, []).append(relic_set)

        # Extend if has more than 2 sets
        if len(grouped_sets) > 2:
            extend_by = (len(grouped_sets) - 2) * (26 + 2)
            delta_extend = extend_by - self._extended_by
            if delta_extend > 0:
                await self._extend_canvas_down(delta_extend)

        for idx, relic_sets in enumerate(grouped_sets.values(), 1):
            select_relic = sorted(relic_sets, key=lambda r: r.need, reverse=True)[0]

            # Create 1:1 box for text
            await self._create_box(
                ((self.RELIC_LEFT, TOP + (idx * 26)), (self.RELIC_LEFT + 20, TOP + (idx * 26) + 20)),
            )
            await self._write_text(
                f"{select_relic.need}",
                (self.RELIC_LEFT + 10.5, TOP + (idx * 26) + 10.5),
                font_size=16,
                use_bg=True,
                anchor="mm",
                align="center",
            )
            # Create the set name
            properties_joined = []
            for prop in select_relic.properties:
                prop_fmt = "{:.1%}" if prop.percent else "{:.0f}"
                properties_joined.append(f"{prop.name} {prop_fmt.format(prop.value)}")
            relic_set_name = select_relic.name
            if properties_joined:
                relic_set_name += " (" + ", ".join(properties_joined) + ")"
            await self._write_text(
                relic_set_name,
                (self.RELIC_LEFT + 21 + 8, TOP + (idx * 26 + 10.5)),
                font_size=16,
                anchor="lm",
                align="left",
            )

    async def _create_planar_and_light_cone(self):
        sorted_relics = sorted(
            self._character.relics,
            key=lambda r: self._relics[r.id].type.order,
        )
        # Group the relics by planar and non-planar
        planar_relics: list[Relic] = []
        for relic in sorted_relics:
            relic_index = self._relics[relic.id]
            if relic_index.type in (SRSRelicType.PlanarOrb, SRSRelicType.PlanarRope):
                planar_relics.append(relic)

        RELIC_LEFT = self.RELIC_LEFT + 138 + 28 + 254 + 60
        if self._character.light_cone is None:
            await self._create_placeholder_slot(1, RELIC_LEFT, text="No Light Cone")
        else:
            light_cone = self._character.light_cone
            cone_stats = [SRSCardStats.from_relic(stats) for stats in light_cone.attributes]
            cone_stats.insert(
                0,
                SRSCardStats(
                    "Level",
                    value=light_cone.level,
                    cut_off=True,
                ),
            )
            await self._create_stats_box(
                position=1,
                left=RELIC_LEFT,
                main_stat=SRSCardStats(
                    light_cone.name,
                    cut_off=True,
                ),
                rarity=light_cone.rarity,
                sub_stats=cone_stats,
                box_icon=light_cone.icon_url,
                box_indicator=f"S{light_cone.superimpose}",
            )

        for idx, relic in enumerate(planar_relics, 2):
            if relic.id == "-1":
                await self._create_placeholder_slot(idx, RELIC_LEFT)
            else:
                await self._create_stats_box(
                    position=idx,
                    left=RELIC_LEFT,
                    main_stat=SRSCardStats.from_relic(relic.main_stats),
                    sub_stats=[SRSCardStats.from_relic(sub) for sub in relic.sub_stats],
                    rarity=relic.rarity,
                    box_icon=relic.icon_url,
                    box_indicator=f"+{relic.level}",
                )

    async def _create_skills_and_traces(self):
        sorted_skills = sorted(
            self._character.skills,
            key=lambda r: r.type.order,
        )
        # Remove the skill of MazeAttack
        sorted_skills = [skill for skill in sorted_skills if skill.type != SkillUsageType.TechniqueAttack]
        # Remove duplicates skill
        sorted_skills = list({skill.type: skill for skill in sorted_skills}.values())

        # We want to autoscale the skills to fit the boundary
        LEFT = 552
        TOP = 658
        SIZE_W = 448

        # Check margin and 1:1 ratio of image size that we need to use
        box_size = 84
        margin = SIZE_W - (box_size * len(sorted_skills)) + (box_size // 2) + 8

        for idx, skill in enumerate(sorted_skills):
            skill_icon = await self._async_open(self._assets_folder / skill.icon_url)
            skill_icon = await self._tint_image(skill_icon, self._foreground)
            skill_icon = await self._loop.run_in_executor(None, skill_icon.resize, (box_size - 4, box_size - 4))

            await self._loop.run_in_executor(
                None,
                self._canvas.paste,
                skill_icon,
                (LEFT + (idx * margin) + 2, TOP),
                skill_icon,
            )
            await self._create_box(
                ((LEFT + (idx * margin) + 2, TOP), (LEFT + (idx * margin) + 36, TOP + 20)),
            )
            value_skill = f"{skill.level:02d}"
            if skill.type == SkillUsageType.Technique:
                value_skill = "YES" if skill.level > 0 else "NO"
            await self._write_text(
                value_skill,
                (LEFT + (idx * margin) + 19, TOP + 11),
                font_size=16,
                anchor="mm",
                use_bg=True,
            )

            await self._write_text(
                skill.type_description,
                (LEFT + (idx * margin) + 2 + (skill_icon.width // 2), TOP + skill_icon.height + 8),
                font_size=14,
                anchor="mm",
            )

        enabled_traces: list[SkillTrace] = []
        for trace in self._character.traces:
            if "skilltree" in trace.icon_url and trace.level > 0:
                enabled_traces.append(trace)

        # We want to autoscale the skills to fit the boundary
        LEFT = 648
        TOP = 760
        SIZE_W = 200

        # Check margin and 1:1 ratio of image size that we need to use
        box_size = 48
        margin = 78

        enabled_traces.sort(key=lambda t: t.icon_url)

        for idx, trace in enumerate(enabled_traces):
            trace_icon = await self._async_open(self._assets_folder / trace.icon_url)
            trace_icon = await self._tint_image(trace_icon, self._foreground)
            trace_icon = await self._loop.run_in_executor(None, trace_icon.resize, (box_size - 4, box_size - 4))

            await self._loop.run_in_executor(
                None,
                self._canvas.paste,
                trace_icon,
                (LEFT + (idx * margin) + 2, TOP),
                trace_icon,
            )

            await self._write_text(
                f"A{(idx + 1) * 2}",
                (LEFT + (idx * margin) + 2 + (trace_icon.width // 2), TOP + trace_icon.height + 10),
                font_size=14,
                anchor="mm",
            )

    async def create(self, *, hide_uid: bool = False, hide_credits: bool = False):
        self._assets_folder = await self._assets_folder.absolute()
        if not await self._assets_folder.exists():
            raise FileNotFoundError("The assets folder does not exist.")
        await self._set_index_properties_name()
        await self._set_index_relics()

        # Calculate average color of the preview image.
        logger.info("Initializing the canvas card information...")
        dominant_and_inversion = _COLOR_DOMINANT.get(self._character.id)
        if dominant_and_inversion is None:
            raise ValueError("The dominant color of the character is missing.")

        # Set the background color to dominant color.
        if isinstance(dominant_and_inversion, list):
            self._canvas.paste(dominant_and_inversion[0], (0, 0, self._canvas.width, self._canvas.height))
            self._foreground = dominant_and_inversion[1]
            self._background = dominant_and_inversion[0]
        else:
            self._canvas.paste(dominant_and_inversion, (0, 0, self._canvas.width, self._canvas.height))
            self._foreground = tuple(255 - c for c in dominant_and_inversion)
            self._background = dominant_and_inversion

        logger.info("Adding player name...")
        middle_bbox_name = self.CHARACTER_TOP // 2
        await self._write_text(
            self._player.name,
            (self.RELIC_LEFT + 140, self.CHARACTER_TOP - middle_bbox_name),
            font_size=72,
            anchor="lm",
        )
        # Player avatar
        avatar_icon = await self._async_open(self._assets_folder / self._player.avatar.icon_url)
        avatar_icon = await self._loop.run_in_executor(
            None,
            avatar_icon.resize,
            (120, 120),
        )
        await self._loop.run_in_executor(
            None,
            self._canvas.paste,
            avatar_icon,
            (self.RELIC_LEFT, self.CHARACTER_TOP - 144),
            avatar_icon,
        )
        await self._loop.run_in_executor(
            None,
            draw_ellipse,
            self._canvas,
            [self.RELIC_LEFT, self.CHARACTER_TOP - 144, self.RELIC_LEFT + 120, self.CHARACTER_TOP - 144 + 120],
            4,
            self._foreground,
            8,
        )

        # Create the character card header.
        logger.info("Creating the character card header...")
        await self._create_character_card_header()
        logger.info("Creating the character card stats...")
        await self._create_character_stats()

        # Create relics sets
        logger.info("Creating the character relics...")
        await self._create_main_relics()
        logger.info("Creating the character planar and light cone...")
        await self._create_planar_and_light_cone()
        logger.info("Creating relic set bonus...")
        await self._create_relic_sets_bonus()

        # Create skills
        logger.info("Creating the character skills...")
        await self._create_skills_and_traces()

        # Create footer
        logger.info("Creating the character footer...")
        await self._write_text(
            "Supported by Interstellar Peace Corporation",
            (20, self._canvas.height - 20),
            font_size=20,
            alpha=128,
            font_path=self._universe_font_path,
            anchor="ls",
        )
        if not hide_credits:
            await self._write_text(
                "Data from Mihomo | Created by @noaione | Idea from StarDB",
                (self._canvas.width - 20, self._canvas.height - 20),
                font_size=20,
                alpha=128,
                anchor="rs",
            )

        # Outer canvas
        main_canvas = Image.new("RGBA", (1600, self._canvas.height + 90), self._foreground)
        # 16px padding left, right, top on where to paste the old canvas
        await self._loop.run_in_executor(
            None,
            main_canvas.paste,
            self._canvas,
            (16, 16),
            self._canvas,
        )
        player_region = get_uid_region(self._player.id)
        starting_foot = self._canvas.height
        height_mid = starting_foot + ((main_canvas.height - starting_foot) // 2) + 8
        player_uid = f"UID: {self._player.id}"
        if player_region is not None:
            player_uid += f" | Region: {player_region}"
        player_uid += f" | Level: {self._player.level:02d}"
        if hide_uid:
            player_uid = f"Level: {self._player.level:02d}"
        await self._write_text(
            player_uid,
            (75, height_mid),
            font_size=30,
            use_bg=True,
            anchor="lm",
            canvas=main_canvas,
        )
        right_side_text = f"Achievements: {self._player.progression.achivements}"
        if self._player.progression.forgotten_hall is not None:
            forgotten_hall = get_actual_moc_floor(self._player.progression.forgotten_hall)
            if forgotten_hall.moc_finished_floor > 0:
                right_side_text = (
                    f"MoC: Floor {forgotten_hall.moc_finished_floor} | {right_side_text}"
                )
        await self._write_text(
            right_side_text,
            (main_canvas.width - 75, height_mid),
            font_size=30,
            use_bg=True,
            anchor="rm",
            canvas=main_canvas,
        )

        # Save the image.
        logger.info("Saving the image...")
        bytes_io = BytesIO()
        await self._loop.run_in_executor(None, main_canvas.save, bytes_io, "PNG")

        logger.info("Cleaning up...")
        await self._loop.run_in_executor(None, main_canvas.close)
        await self._loop.run_in_executor(None, self._canvas.close)

        # Return the bytes.
        bytes_io.seek(0)
        all_bytes = await self._loop.run_in_executor(None, bytes_io.read)
        bytes_io.close()
        return all_bytes
