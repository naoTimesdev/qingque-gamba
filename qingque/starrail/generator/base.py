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
import math
from collections.abc import MutableMapping
from io import BytesIO
from logging import Logger, LoggerAdapter
from typing import Any, TypeAlias, cast

from aiopath import AsyncPath
from PIL import Image, ImageDraw, ImageFont, ImageOps

from qingque.hylab.models.base import HYLanguage
from qingque.i18n import QingqueLanguage, get_i18n
from qingque.mihomo.models.constants import MihomoLanguage

from ..loader import SRSDataLoader

__all__ = (
    "StarRailDrawing",
    "StarRailDrawingLogger",
    "RGB",
)
RGB: TypeAlias = tuple[int, int, int]


def euclidean_distance(ax: float, ay: float, bx: float, by: float) -> float:
    """Find the euclidean distance between 2d points."""
    return math.sqrt((by - ay) ** 2 + (bx - ax) ** 2)


def rotate_square_points(ax: float, ay: float, bx: float, by: float, angle: int | float) -> tuple[int, int]:
    """Rotate a point around another point."""
    radius = euclidean_distance(ax, ay, bx, by)
    angle += math.atan2(ay - by, ax - bx)
    return (round(bx + radius * math.cos(angle)), round(by + radius * math.sin(angle)))


class StarRailDrawingLogger(LoggerAdapter):
    def __init__(self, logger: Logger, *, metadata: str) -> None:
        super().__init__(logger, {})
        self.metadata = metadata

    def process(self, msg: Any, kwargs: MutableMapping[str, Any]) -> tuple[Any, MutableMapping[str, Any]]:
        return "[%s] %s" % (self.metadata, msg), kwargs

    @classmethod
    def create(cls: type[StarRailDrawingLogger], metadata: str) -> type[StarRailDrawingLogger]:
        return cast(type[StarRailDrawingLogger], functools.partial(cls, metadata=metadata))


class StarRailDrawing:
    _canvas: Image.Image

    def __init__(self, *, language: MihomoLanguage | HYLanguage | QingqueLanguage = MihomoLanguage.EN) -> None:
        if isinstance(language, HYLanguage):
            language = language.mihomo
        elif isinstance(language, QingqueLanguage):
            language = language.to_mihomo()
        self._language: MihomoLanguage = language if isinstance(language, MihomoLanguage) else language.mihomo
        self._loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        if isinstance(language, QingqueLanguage):
            self._i18n = get_i18n().copy(language)
        else:
            self._i18n = get_i18n().copy(QingqueLanguage.from_mihomo(self._language))

        self._assets_folder = AsyncPath(__file__).parent.parent.parent / "assets" / "srs"
        self._index_data: SRSDataLoader = SRSDataLoader(self._language)

        self._foreground: RGB = (255, 255, 255)
        self._background: RGB = (0, 0, 0)
        self._font_path: AsyncPath = self._assets_folder / ".." / "fonts" / "SDK_SC_Web.ttf"
        self._universe_font_path: AsyncPath = self._assets_folder / ".." / "fonts" / "FirstWorld.ttf"

        self._extend_down_by: int = 0
        self._extend_right_by: int = 0

    def _make_canvas(self, *, width: int, height: int, color: RGB = (255, 255, 255)) -> None:
        self._canvas = Image.new("RGBA", (width, height), color)

    def has_canvas(self) -> bool:
        return hasattr(self, "_canvas")

    async def _create_font(self, font_path: AsyncPath, size: int = 20) -> ImageFont.FreeTypeFont:
        font = await self._loop.run_in_executor(None, ImageFont.truetype, str(font_path), size)
        return font

    async def _get_draw(self, *, canvas: Image.Image | None = None) -> ImageDraw.ImageDraw:
        if not self.has_canvas() and canvas is None:
            raise RuntimeError("Canvas is not initialized, and no canvas is provided.")
        canvas = canvas or self._canvas
        return await self._loop.run_in_executor(None, ImageDraw.Draw, canvas)

    async def _extend_canvas_down(self, height: int) -> None:
        if not self.has_canvas():
            raise RuntimeError("Canvas is not initialized.")

        new_canvas = Image.new("RGBA", (self._canvas.width, self._canvas.height + height), (255, 255, 255))
        # Paste background
        await self._paste_image(
            self._background,
            (0, 0, new_canvas.width, new_canvas.height),
            canvas=new_canvas,
        )
        # Paste canvas
        await self._paste_image(self._canvas, (0, 0), canvas=new_canvas)
        self._canvas = new_canvas
        self._extend_down_by += height

    async def _extend_canvas_right(self, width: int) -> None:
        if not self.has_canvas():
            raise RuntimeError("Canvas is not initialized.")

        new_canvas = Image.new("RGBA", (self._canvas.width + width, self._canvas.height), (255, 255, 255))
        # Paste background
        await self._paste_image(
            self._background,
            (0, 0, new_canvas.width, new_canvas.height),
            canvas=new_canvas,
        )
        # Paste canvas
        await self._paste_image(self._canvas, (0, 0), canvas=new_canvas)
        self._canvas = new_canvas
        self._extend_right_by += width

    async def _write_text(
        self,
        content: str,
        box: tuple[float, float] | tuple[float, float, float, float],
        font_size: int = 20,
        font_path: AsyncPath | None = None,
        color: RGB | None = None,
        no_elipsis: bool = False,
        alpha: int = 255,
        *,
        canvas: Image.Image | None = None,
        **kwargs: Any,
    ) -> float:
        if not self.has_canvas() and canvas is None:
            raise RuntimeError("Canvas is not initialized, and no canvas is provided.")
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

        fill = color or self._foreground
        draw_text = functools.partial(draw.text, fill=(*fill, alpha), font=font, **kwargs)
        await self._loop.run_in_executor(None, draw_text, box, content)
        length_width = await self._loop.run_in_executor(None, draw.textlength, content, font)
        if composite is not None:
            await self._loop.run_in_executor(None, canvas.alpha_composite, composite)
        return length_width

    async def _create_box(
        self,
        box: tuple[tuple[float, float], tuple[float, float]],
        color: RGB | None = None,
        width: int = 0,
        angle: int | float = 0,
        antialias: int = 4,
        *,
        resampling: Image.Resampling = Image.Resampling.LANCZOS,
        canvas: Image.Image | None = None,
    ) -> None:
        """
        Create a box on the canvas.

        Parameters
        ----------
        box: :class:`tuple[tuple[float, float], tuple[float, float]]`
            The box boundary to create. (top-left, bottom-right)
        color: :class:`tuple[int, int, int]`
            The color of the box.
        width: :class:`int`
            The width of the box, if applied will be created as a outlined rectangle instead
            of a filled rectangle.
        angle: :class:`int` | :class:`float`
            The angle to rotate the box.
        antialias: :class:`int`
            The antialiasing level to use when drawing the box, will not be applied if angle is 0.0.
        resampling: :class:`PIL.Image.Resampling`
            The resampling method to use when resizing the mask.
            Used with anti-aliasing. Defaults to :class:`PIL.Image.LANCZOS`.
        canvas: :class:`PIL.Image.Image`
            The canvas to draw on, defaults to the current canvas.
        """

        if not self.has_canvas() and canvas is None:
            raise RuntimeError("Canvas is not initialized, and no canvas is provided.")

        canvas = canvas or self._canvas

        # Use a single channel image (mode='L') as mask.
        # The size of the mask can be increased relative to the imput image
        # to get smoother looking results.
        canvas_size: tuple[int, int] = (int(canvas.width * antialias), int(canvas.height * antialias))
        if angle == 0.0:
            # Disable AA if angle is 0.0
            canvas_size = canvas.size
            antialias = 1
        mask = Image.new(size=canvas_size, mode="L", color="black")
        draw = await self._get_draw(canvas=mask)

        fill = color or self._foreground

        square_verticies: list[tuple[float, float]] = [
            (box[0][0], box[0][1]),
            (box[0][0], box[1][1]),
            (box[1][0], box[1][1]),
            (box[1][0], box[0][1]),
        ]
        # Multiply the verticies by antialias
        square_verticies = [(x * antialias, y * antialias) for x, y in square_verticies]
        if angle != 0.0:
            square_center = (
                (box[0][0] + box[1][0]) / 2,
                (box[0][1] + box[1][1]) / 2,
            )
            square_verticies = [
                rotate_square_points(x, y, square_center[0], square_center[1], math.radians(angle))
                for x, y in square_verticies
            ]
        # Draw it with anti-aliasing, put it in mask where white will be where the square would be.
        if width > 0.0:
            draw_polygon = functools.partial(draw.polygon, fill=None, outline="white", width=width * antialias)
        else:
            draw_polygon = functools.partial(draw.polygon, fill="white", outline=None, width=width)
        await self._loop.run_in_executor(None, draw_polygon, square_verticies)
        # Downsample the mask if angle is not 0.0
        if angle != 0.0:
            mask = await self._loop.run_in_executor(None, mask.resize, canvas.size, resampling)
        await self._paste_image(fill, mask=mask, canvas=canvas)

    async def _create_circle(
        self,
        bounds: list[int],
        width: int = 1,
        outline: RGB = (255, 255, 255),
        antialias: int = 4,
        *,
        canvas: Image.Image | None = None,
    ) -> None:
        """Improved ellipse drawing function, based on PIL.ImageDraw.

        Source: https://stackoverflow.com/a/34926008
        """

        if not self.has_canvas() and canvas is None:
            raise RuntimeError("Canvas is not initialized, and no canvas is provided.")

        canvas = canvas or self._canvas

        # Use a single channel image (mode='L') as mask.
        # The size of the mask can be increased relative to the imput image
        # to get smoother looking results.
        mask = Image.new(size=[int(dim * antialias) for dim in canvas.size], mode="L", color="black")  # type: ignore
        draw = await self._get_draw(canvas=mask)

        # draw outer shape in white (color) and inner shape in black (transparent)
        for offset, fill in (width / -2.0, "white"), (width / 2.0, "black"):
            left, top = [(value + offset) * antialias for value in bounds[:2]]
            right, bottom = [(value - offset) * antialias for value in bounds[2:]]
            await self._loop.run_in_executor(None, draw.ellipse, [left, top, right, bottom], fill)

        # downsample the mask using PIL.Image.LANCZOS
        # (a high-quality downsampling filter).
        mask = await self._loop.run_in_executor(None, mask.resize, canvas.size, Image.LANCZOS)
        # paste outline color to input image through the mask
        await self._paste_image(outline, mask=mask, canvas=canvas)

    async def _tint_image(self, im: Image.Image, color: RGB) -> Image.Image:
        alpha = im.split()[3]
        gray = await self._loop.run_in_executor(None, ImageOps.grayscale, im)
        result = await self._loop.run_in_executor(None, ImageOps.colorize, gray, color, color)
        await self._loop.run_in_executor(None, result.putalpha, alpha)
        return result

    async def _paste_image(
        self,
        img: Image.Image | RGB,
        box: tuple[float, float] | tuple[float, float, float, float] | None = None,
        mask: Image.Image | None = None,
        *,
        canvas: Image.Image | None = None,
    ) -> None:
        if not self.has_canvas() and canvas is None:
            raise RuntimeError("Canvas is not initialized, and no canvas is provided.")
        canvas = canvas or self._canvas
        await self._loop.run_in_executor(None, canvas.paste, img, box, mask)

    async def _crop_image(self, img: Image.Image, box: tuple[float, float, float, float]) -> Image.Image:
        return await self._loop.run_in_executor(None, img.crop, box)

    async def _resize_image(self, img: Image.Image, size: tuple[int, int]) -> Image.Image:
        return await self._loop.run_in_executor(None, img.resize, size)

    async def _async_open(self, img_path: AsyncPath) -> Image.Image:
        io = BytesIO()
        read_data = await img_path.read_bytes()
        io.write(read_data)
        io.seek(0)
        # Open as RGBA in case the image is transparent.
        as_image = (await self._loop.run_in_executor(None, Image.open, io)).convert("RGBA")
        return as_image

    async def _async_save_bytes(self, canvas: Image.Image) -> BytesIO:
        io = BytesIO()
        await self._loop.run_in_executor(None, canvas.save, io, "PNG")
        io.seek(0)
        return io

    async def _async_close(self, canvas: Image.Image) -> None:
        await self._loop.run_in_executor(None, canvas.close)

    async def create(self, **kwargs: Any) -> bytes:
        """
        Create the card.
        """
        raise NotImplementedError
