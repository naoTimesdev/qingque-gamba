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

from PIL import ImageEnhance

from qingque.hylab.models.forgotten_hall import ChronicleFHFloor, ChronicleFHNode
from qingque.mihomo.models.constants import MihomoLanguage
from qingque.starrail.imaging import AsyncImageEnhance
from qingque.tooling import get_logger

from .base import StarRailDrawing, StarRailDrawingLogger
from .mixins import SRDrawCharacter, StarRailDrawCharacterMixin, StarRailDrawGradientMixin

if TYPE_CHECKING:
    from qingque.hylab.models.base import HYLanguage
    from qingque.i18n import QingqueLanguage
    from qingque.starrail.loader import SRSDataLoader

__all__ = ("StarRailMoCCard",)


class StarRailMoCCard(StarRailDrawGradientMixin, StarRailDrawCharacterMixin, StarRailDrawing):
    MARGIN_LR = 75
    MARGIN_TB = 75

    def __init__(
        self,
        floor: ChronicleFHFloor,
        *,
        language: MihomoLanguage | HYLanguage | QingqueLanguage = MihomoLanguage.EN,
        loader: SRSDataLoader | None = None,
    ) -> None:
        super().__init__(language=language, loader=loader)
        self._floor: ChronicleFHFloor = floor
        self.logger = get_logger(
            "qingque.starrail.generator.moc",
            adapter=StarRailDrawingLogger.create(f"FH-{floor.name}"),
        )

        self._background = (0, 0, 0)
        self._foreground = (255, 255, 255)
        self._make_canvas(width=1920, height=665, color=self._background)

    async def _create_backdrops(self):
        backdrops = self._assets_folder / "image" / "backdrops" / "BackdropAbyss.png"
        # Open the backdrop image.
        backdrop_img = await self._async_open(backdrops)
        enhancer = AsyncImageEnhance(backdrop_img, subclass=ImageEnhance.Brightness)
        # Lower the brightness of the backdrop.
        backdrop_img = await enhancer.enhance(0.5)
        # Paste the backdrop image to the canvas.
        await self._paste_image(backdrop_img, (0, 0))
        await self._async_close(backdrop_img)

    async def _create_node(self, node: ChronicleFHNode, node_name: str, margin_left: int):
        inbetween_margin = 180
        INITIAL_TOP = self.MARGIN_TB + 260

        characters = [SRDrawCharacter.from_hylab(c) for c in node.characters]

        await self._write_text(
            node_name,
            (margin_left, INITIAL_TOP - 25),
            font_size=32,
            color=self._foreground,
            anchor="ls",
            alpha=round(0.85 * 255),
        )
        await self._create_character_card(
            characters,
            margin_top=INITIAL_TOP,
            margin_lr=margin_left,
            inbetween_margin=inbetween_margin,
            icon_size=150,
            drawing=self,
            box_color=(*self._background, round(0.65 * 255)),
            box_text_color=self._foreground,
        )

    async def _create_nodes(self):
        # Create first node
        await self._create_node(
            self._floor.node_1,
            self._i18n.t("chronicles.moc_top"),
            self.MARGIN_LR,
        )
        # Create second node (right to left)
        second_node_margin = self._canvas.width - self.MARGIN_LR - (4 * (150 + 30)) + 30
        await self._create_node(
            self._floor.node_2,
            self._i18n.t("chronicles.moc_bottom"),
            second_node_margin,
        )

    async def _create_stars_cycles(self):
        # If stars, use image, if no use TL.
        if self._floor.stars_total > 0:
            MARGINAL = 100
            stars_icon = await self._async_open(self._assets_folder / "icon" / "deco" / "StarBig.png")
            # Resize to 120x120
            stars_icon = await self._resize_image(stars_icon, (120, 120))
            # Paste the stars icon, from top right moving to left.
            for i in range(self._floor.stars_total):
                await self._paste_image(
                    stars_icon,
                    (
                        self._canvas.width - 172 - (i * 120),
                        self.MARGIN_TB,
                    ),
                    stars_icon,
                )
            await self._async_close(stars_icon)
        else:
            # Create a no star icon
            MARGINAL = 80
            await self._write_text(
                self._i18n.t("chronicles.moc_no_stars"),
                (self._canvas.width - self.MARGIN_LR, self.MARGIN_TB + 76),
                font_size=60,
                color=self._foreground,
                anchor="rs",
                align="right",
                alpha=round(0.85 * 255),
            )

        # Create the cycles text
        await self._write_text(
            self._i18n.t("chronicles.moc_cycles", [f"{self._floor.round_total:,}"]),
            (self._canvas.width - self.MARGIN_LR, self.MARGIN_TB + 76 + MARGINAL),
            font_size=42,
            color=self._foreground,
            anchor="rs",
            align="right",
            alpha=round(0.8 * 255),
        )

    async def create(self, *, hide_credits: bool = False, hide_timestamp: bool = False) -> bytes:
        self._assets_folder = await self._assets_folder.absolute()
        if not await self._assets_folder.exists():
            raise FileNotFoundError("The assets folder does not exist.")
        await self._index_data.async_loads()

        self.logger.info("Creating background/backdrops...")
        await self._create_backdrops()

        self.logger.info("Creating floor name...")
        await self._write_text(
            self._i18n.t("chronicles.moc"),
            (self.MARGIN_LR, self.MARGIN_TB + 72),
            font_size=75,
            color=self._foreground,
            anchor="ls",
            alpha=round(0.95 * 255),
        )
        # Floor name
        await self._write_text(
            self._floor.name,
            (self.MARGIN_LR, self.MARGIN_TB + 75 + 80),
            font_size=42,
            color=self._foreground,
            anchor="ls",
            alpha=round(0.9 * 255),
        )

        self.logger.info("Creating nodes...")
        await self._create_nodes()

        self.logger.info("Creating stars and cycles...")
        await self._create_stars_cycles()

        self.logger.info("Creating footer...")
        await self._write_text(
            "Supported by Interastral Peace Corporation",
            (20, self._canvas.height - 20),
            font_size=20,
            alpha=round(0.35 * 255),
            font_path=self._universe_font_path,
            anchor="ls",
        )
        if not hide_credits:
            await self._write_text(
                self._i18n.t("chronicles.credits"),
                (self._canvas.width - 20, self._canvas.height - 20),
                font_size=16,
                alpha=round(0.35 * 255),
                anchor="rs",
                align="right",
            )

        # Create a timestamp (bottom middle)
        if not hide_timestamp:
            await self._write_text(
                f"{self.format_timestamp(self._floor.node_1.challenge_time.datetime)}",
                (self._canvas.width // 2, self._canvas.height - 20),
                font_size=20,
                anchor="ms",
                alpha=round(0.35 * 255),
            )

        # Save the image.
        self.logger.info("Saving the image...")
        bytes_io = await self._async_save_bytes(self._canvas)

        self.logger.info("Cleaning up...")
        await self._async_close(self._canvas)
        await self.close()

        # Return the bytes.
        bytes_io.seek(0)
        all_bytes = await self._loop.run_in_executor(None, bytes_io.read)
        bytes_io.close()
        return all_bytes
