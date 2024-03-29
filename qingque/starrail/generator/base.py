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
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime, timezone
from io import BytesIO
from logging import Logger, LoggerAdapter
from typing import Any, Callable, Literal, TypeAlias, cast

from aiopath import AsyncPath
from babel import Locale
from babel.dates import format_date, format_time
from babel.numbers import format_decimal, format_percent
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps
from PIL._util import DeferredError

from qingque.hylab.models.base import HYLanguage
from qingque.i18n import QingqueLanguage, get_i18n
from qingque.mihomo.models.constants import MihomoLanguage
from qingque.starrail.caching import StarRailImageCache
from qingque.starrail.imaging import AsyncImageEnhance

from ..loader import SRSDataLoader

__all__ = (
    "StarRailDrawing",
    "StarRailDrawingLogger",
    "RGB",
)
RGBA: TypeAlias = tuple[int, int, int, int]
RGB: TypeAlias = tuple[int, int, int]
Number: TypeAlias = int | float


def euclidean_distance(ax: float, ay: float, bx: float, by: float) -> float:
    """Find the euclidean distance between 2d points."""
    return math.sqrt((by - ay) ** 2 + (bx - ax) ** 2)


def rotate_square_points(ax: float, ay: float, bx: float, by: float, angle: int | float) -> tuple[int, int]:
    """Rotate a point around another point."""
    radius = euclidean_distance(ax, ay, bx, by)
    angle += math.atan2(ay - by, ax - bx)
    return (round(bx + radius * math.cos(angle)), round(by + radius * math.sin(angle)))


class StarRailDrawingLogger(LoggerAdapter):
    """A logger adapter for StarRailDrawing."""

    def __init__(self, logger: Logger, *, metadata: str) -> None:
        super().__init__(logger, {})
        self.metadata = metadata

    def process(self, msg: Any, kwargs: MutableMapping[str, Any]) -> tuple[Any, MutableMapping[str, Any]]:
        return "[%s] %s" % (self.metadata, msg), kwargs

    @classmethod
    def create(cls: type[StarRailDrawingLogger], metadata: str) -> type[StarRailDrawingLogger]:
        return cast(type[StarRailDrawingLogger], functools.partial(cls, metadata=metadata))


def get_babel_locale(language: MihomoLanguage):
    match language:
        case MihomoLanguage.CHS:
            return Locale("zh_Hans")
        case MihomoLanguage.CHT:
            return Locale("zh_Hant")
        case MihomoLanguage.DE:
            return Locale("de")
        case MihomoLanguage.EN:
            return Locale("en", "US")
        case MihomoLanguage.ES:
            return Locale("es", "ES")
        case MihomoLanguage.FR:
            return Locale("fr")
        case MihomoLanguage.ID:
            return Locale("id")
        case MihomoLanguage.JP:
            return Locale("ja")
        case MihomoLanguage.KR:
            return Locale("ko")
        case MihomoLanguage.PT:
            return Locale("pt")
        case MihomoLanguage.RU:
            return Locale("ru")
        case MihomoLanguage.TH:
            return Locale("th")
        case MihomoLanguage.VI:
            return Locale("vi")


class StarRailDrawing:
    """The base class for drawing Honkai: Star Rail profile cards.

    Raises
    ------
    :class:`RuntimeError`
        Canvas is not initialized, and no canvas is provided.
    """

    _canvas: Image.Image

    def __init__(
        self,
        *,
        language: MihomoLanguage | HYLanguage | QingqueLanguage = MihomoLanguage.EN,
        loader: SRSDataLoader | None = None,
        img_cache: StarRailImageCache | None = None,
        executor: ProcessPoolExecutor | ThreadPoolExecutor | None = None,
    ) -> None:
        """Initialize the asynchronous drawing mechanism.

        Parameters
        ----------
        language: :class:`MihomoLanguage` | :class`HYLanguage` | :class`QingqueLanguage`, optional
            The language to use, by default MihomoLanguage.EN
        loader: :class:`SRSDataLoader` | :class:`None`, optional
            The data loader, can be passed to reuse the same data loader, by default None
        """

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
        self._index_data: SRSDataLoader = loader or SRSDataLoader(self._language)
        if loader is not None:
            if self._index_data.language != self._language:
                self._index_data.unloads()
                self._index_data.language = self._language

        self._foreground: RGB = (255, 255, 255)
        self._background: RGB = (0, 0, 0)
        self._font_path: AsyncPath = self._assets_folder / ".." / "fonts" / "SDK_SC_Web.ttf"
        self._universe_font_path: AsyncPath = self._assets_folder / ".." / "fonts" / "FirstWorld.ttf"

        self._extend_down_by: int = 0
        self._extend_right_by: int = 0

        self._img_cache = img_cache or StarRailImageCache()
        self.__executor = executor or ThreadPoolExecutor(
            max_workers=8, thread_name_prefix=self.__class__.__name__ + "-thread"
        )

    @property
    def executor(self) -> ProcessPoolExecutor | ThreadPoolExecutor:
        """:class:`ProcessPoolExecutor` | :class:`ThreadPoolExecutor`: The executor used for drawing."""
        return self.__executor

    def _make_canvas(self, *, width: int, height: int, color: int | RGB | RGBA = (255, 255, 255)) -> None:
        """Create the base canvas.

        Parameters
        ----------
        width: :class:`int`
            The width of the canvas.
        height: :class:`int`
            The height of the canvas.
        color: :class:`int` | :class:`RGB`, optional
            The tuple or single number of the initial color, by default (255, 255, 255)
        """

        self._canvas = Image.new("RGBA", (width, height), color)

    def has_canvas(self) -> bool:
        """
        Check if the canvas is initialized.

        Returns
        -------
        :class:`bool`
            Whether the canvas is initialized.
        """

        return hasattr(self, "_canvas")

    async def _create_font(self, font_path: AsyncPath, size: int = 20) -> ImageFont.FreeTypeFont:
        """Create a free type font to be used to writing text.

        Parameters
        ----------
        font_path: :class:`AsyncPath`
            The font path.
        size: :class:`int`, optional
            The font size, by default 20

        Returns
        -------
        :class:`ImageFont.FreeTypeFont`
            The font object.
        """

        font = await self._loop.run_in_executor(self.__executor, ImageFont.truetype, str(font_path), size)
        return font

    async def _get_draw(self, *, canvas: Image.Image | None = None) -> ImageDraw.ImageDraw:
        """Get the draw object for a canvas.

        Parameters
        ----------
        canvas: :class:`Image.Image` | None, optional
            The canvas you want to get the draw object from, default to the base canvas.

        Returns
        -------
        :class:`ImageDraw.ImageDraw`
            The draw object of a canvas.

        Raises
        ------
        :class:`RuntimeError`
            Canvas is not initialized, and no canvas is provided.
        """

        if not self.has_canvas() and canvas is None:
            raise RuntimeError("Canvas is not initialized, and no canvas is provided.")
        canvas = canvas or self._canvas
        return await self._loop.run_in_executor(self.__executor, ImageDraw.Draw, canvas)

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
        color: RGB | int | None = None,
        no_elipsis: bool = False,
        alpha: int = 255,
        stroke: int = 0,
        stroke_color: RGB | int | None = None,
        *,
        canvas: Image.Image | None = None,
        **kwargs: Any,
    ) -> float:
        """Write a text into the canvas, with automatic elipsis application and cut off.

        Parameters
        ----------
        content: :class:`str`
            The content to write.
        box: :class:`tuple[float, float]` | :class:`tuple[float, float, float, float]`
            The box boundary to write. (top-left, bottom-right) or (top-left, top-right, bottom-left, bottom-right).
            If using the later, the text will be cut off if it exceeds the box.
        font_size: :class:`int`, optional
            The font size, by default 20
        font_path: :class:`AsyncPath` | None, optional
            The font path, by default None
        color: :class:`tuple[int, int, int]` | None, optional
            The color of the text, by default None
        no_elipsis: :class:`bool`, optional
            Whether to disable applying an elipsis `...` to the text when it exceeds the box, by default False
        alpha: :class:`int`, optional
            The alpha of the text, by default 255
        canvas: :class:`Image.Image` | None, optional
            The canvas you want to get the draw object from, default to the base canvas.
        kwargs: :class:`Any`
            The keyword arguments to pass to the draw.text function.

        Returns
        -------
        :class:`float`
            The length of the text.

        Raises
        ------
        :class:`RuntimeError`
            Canvas is not initialized, and no canvas is provided.
        """

        if not self.has_canvas() and canvas is None:
            raise RuntimeError("Canvas is not initialized, and no canvas is provided.")
        kwargs.pop("fill", None)
        kwargs.pop("font", None)
        kwargs.pop("xy", None)
        kwargs.pop("text", None)
        kwargs.pop("stroke_width", None)
        kwargs.pop("stroke_fill", None)
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
        if not isinstance(color, int) and alpha < 255:
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
            text_width = await self._loop.run_in_executor(self.__executor, draw.textlength, content, font)
            while text_width > box_width:
                # Cut off content + ...
                content = content[:-1]
                if not content:
                    break
                tst_content = content + " ..." if not no_elipsis else content
                text_width = await self._loop.run_in_executor(self.__executor, draw.textlength, tst_content, font)
            if not no_elipsis and original_content != content:
                content += " ..."

        fill = color or self._foreground
        fill_col = fill
        if isinstance(fill, tuple):
            fill_col = (*fill[:3], alpha)
        draw_text = functools.partial(
            draw.text, fill=fill_col, font=font, stroke_width=stroke, stroke_fill=stroke_color, **kwargs
        )
        await self._loop.run_in_executor(self.__executor, draw_text, box, content)
        length_width = await self._loop.run_in_executor(self.__executor, draw.textlength, content, font)
        if composite is not None:
            await self._loop.run_in_executor(self.__executor, canvas.alpha_composite, composite)
        return length_width

    async def _calc_text(
        self,
        content: str,
        font_size: int = 20,
        font_path: AsyncPath | None = None,
        *,
        canvas: Image.Image | None = None,
        direction: Literal["ltr", "rtl"] = "ltr",
    ) -> float:
        """Calculate how much space a text will take.

        Parameters
        ----------
        content: :class:`str`
            The content to write.
        font_size: :class:`int`, optional
            The font size, by default 20
        font_path: :class:`AsyncPath` | None, optional
            The font path, by default None
        canvas: :class:`Image.Image` | None, optional
            The canvas you want to get the draw object from, default to the base canvas.
        direction: :class:`Literal["ltr", "rtl"]`, optional
            The direction of the text, by default "ltr"

        Returns
        -------
        :class:`float`
            The length of the text.

        Raises
        ------
        :class:`RuntimeError`
            Canvas is not initialized, and no canvas is provided.
        """

        if not self.has_canvas() and canvas is None:
            raise RuntimeError("Canvas is not initialized, and no canvas is provided.")
        canvas = canvas or self._canvas

        font_path = font_path or self._font_path
        font = await self._create_font(font_path, font_size)

        draw = await self._get_draw(canvas=canvas)
        return await self._loop.run_in_executor(
            None,
            draw.textlength,
            content,
            font,
            direction,
        )

    async def _create_box(
        self,
        box: tuple[tuple[float, float], tuple[float, float]],
        color: RGB | RGBA | None = None,
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

        Raises
        ------
        :class:`RuntimeError`
            Canvas is not initialized, and no canvas is provided.
        """

        if not self.has_canvas() and canvas is None:
            raise RuntimeError("Canvas is not initialized, and no canvas is provided.")

        canvas = canvas or self._canvas
        fill = color or self._foreground

        # Use a single channel image (mode='L') as mask.
        # The size of the mask can be increased relative to the imput image
        # to get smoother looking results.
        canvas_size: tuple[int, int] = (int(canvas.width * antialias), int(canvas.height * antialias))
        if angle == 0.0:
            # Disable AA if angle is 0.0
            canvas_size = canvas.size
            antialias = 1
        fill_overlay = fill
        if len(fill) == 3:
            fill_overlay += (0,)
        else:
            fill_overlay = fill_overlay[:3] + (0,)
        overlay = Image.new("RGBA", canvas_size, cast(RGBA, fill_overlay))
        mask = Image.new(size=canvas_size, mode="L", color="black")
        draw = await self._get_draw(canvas=mask)

        square_verticies: list[tuple[float, float]] = [
            (box[0][0], box[0][1]),
            (box[0][0], box[1][1] - 1),
            (box[1][0] - 1, box[1][1] - 1),
            (box[1][0] - 1, box[0][1]),
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
        await self._loop.run_in_executor(self.__executor, draw_polygon, square_verticies)
        # Downsample the mask if angle is not 0.0
        if angle != 0.0:
            mask = await self._resize_image(mask, canvas.size, resampling=resampling)
        # Paste into overlay first for compositing
        await self._paste_image(fill, mask=mask, canvas=overlay)
        await self._loop.run_in_executor(self.__executor, canvas.alpha_composite, overlay)

    async def _create_box_2_gradient(
        self,
        bounds: tuple[Number, Number, Number, Number],
        colors: tuple[RGB, RGB],
        movement: Literal["hor", "vert"] = "vert",
        *,
        canvas: Image.Image | None = None,
    ) -> None:
        """Create a box with 2 color gradient.

        Parameters
        ----------
        bounds: :class:`tuple[Number, Number, Number, Number]`
            The box boundary to create. (top-left, bottom-right)
        colors: :class:`tuple[RGB, RGB]`
            The colors of the gradient.
        movement: :class:`Literal["hor", "vert"]`, optional
            The direction of the gradient, by default "vert"
        canvas: :class:`PIL.Image.Image`
            The canvas to draw on, defaults to the current canvas.

        Raises
        ------
        :class:`RuntimeError`
            Canvas is not initialized, and no canvas is provided.
        """

        canvas = canvas or self._canvas
        width = int(round(bounds[2] - bounds[0]))
        height = int(round(bounds[3] - bounds[1]))
        base = Image.new("RGB", (width, height), colors[0])
        top = Image.new("RGB", (width, height), colors[1])
        mask = Image.new("L", (width, height))
        mask_data = []
        for y in range(height):
            mask_data.extend([int(255 * (y / height))] * width)  # type: ignore
        if movement == "hor":
            # Transpose the mask data
            mask_data = [mask_data[y::height] for y in range(height)]
            # Flatten the mask data
            mask_data = [item for sublist in mask_data for item in sublist]
        await self._loop.run_in_executor(
            None,
            mask.putdata,
            mask_data,
        )
        await self._paste_image(
            top,
            (0, 0),
            mask,
            canvas=base,
        )
        await self._paste_image(base, (bounds[0], bounds[1]), canvas=canvas)

    async def _create_circle(
        self,
        bounds: list[int],
        width: int = 1,
        color: RGB | RGBA = (255, 255, 255),
        antialias: int = 4,
        *,
        canvas: Image.Image | None = None,
    ) -> None:
        """Create a circle on the canvas.

        This version of the function is better than the original one, since it uses
        anti-aliasing to create a smoother outline.

        Source: https://stackoverflow.com/a/34926008

        Parameters
        ----------
        bounds: :class:`list[int]`
            The bounds of the circle. (left, top, right, bottom)
        width: :class:`int`, optional
            The width of the circle (outline), by default 1
        color: :class:`tuple[int, int, int]`, optional
            The color of the circle, by default (255, 255, 255)
        antialias: :class:`int`, optional
            The antialiasing level to use when drawing the box, by default 4
        canvas: :class:`PIL.Image.Image`
            The canvas to draw on, defaults to the current canvas.

        Raises
        ------
        :class:`RuntimeError`
            Canvas is not initialized, and no canvas is provided.
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
        if width > 0:
            for offset, fill in (width / -2.0, "white"), (width / 2.0, "black"):
                left, top = [(value + offset) * antialias for value in bounds[:2]]
                right, bottom = [(value - offset) * antialias for value in bounds[2:]]
                await self._loop.run_in_executor(self.__executor, draw.ellipse, [left, top, right, bottom], fill)
        else:
            await self._loop.run_in_executor(
                self.__executor, draw.ellipse, [value * antialias for value in bounds], "white"
            )

        # downsample the mask using PIL.Image.LANCZOS
        # (a high-quality downsampling filter).
        mask = await self._resize_image(mask, canvas.size, resampling=Image.Resampling.LANCZOS)
        # paste outline color to input image through the mask
        fill_overlay = color
        if len(color) == 3:
            fill_overlay += (0,)
        else:
            fill_overlay = fill_overlay[:3] + (0,)
        overlay = Image.new("RGBA", canvas.size, cast(RGBA, fill_overlay))
        await self._paste_image(color, mask=mask, canvas=overlay)
        # Paste the overlay onto the canvas
        await self._loop.run_in_executor(self.__executor, canvas.alpha_composite, overlay)

    async def _create_line(
        self,
        points: tuple[float, float, float, float],
        width: int = 1,
        color: RGB | RGBA | None = None,
        antialias: int = 4,
        *,
        canvas: Image.Image | None = None,
    ) -> None:
        """Draw a line on the canvas.

        Parameters
        ----------
        points: :class:`tuple[float, float, float, float]`
            The points to draw the line. (x1, y1, x2, y2)
        width: :class:`int`, optional
            The width of the line, by default 1
        color: :class:`RGB | RGBA | None`, optional
            The color of the line, by default the foreground color.
        antialias: :class:`int`, optional
            The antialiasing level to use when drawing the box, by default 4
        canvas: :class:`PIL.Image.Image`
            The canvas to draw on, defaults to the current canvas.

        Raises
        ------
        :class:`RuntimeError`
            Canvas is not initialized, and no canvas is provided.
        """

        if not self.has_canvas() and canvas is None:
            raise RuntimeError("Canvas is not initialized, and no canvas is provided.")

        canvas = canvas or self._canvas
        color = color or self._foreground

        # Use a single channel image (mode='L') as mask.
        # The size of the mask can be increased relative to the imput image
        # to get smoother looking results.
        mask = Image.new(size=[int(dim * antialias) for dim in canvas.size], mode="L", color="black")  # type: ignore
        draw = await self._get_draw(canvas=mask)

        line_draw = functools.partial(draw.line, fill="white", width=width * antialias)
        act_points = tuple(point * antialias for point in points)
        await self._loop.run_in_executor(self.__executor, line_draw, act_points)

        # downsample the mask using PIL.Image.LANCZOS
        # (a high-quality downsampling filter).
        mask = await self._resize_image(mask, canvas.size, resampling=Image.Resampling.LANCZOS)
        # paste color to input image through the mask
        fill_overlay = color
        if len(color) == 3:
            fill_overlay += (0,)
        else:
            fill_overlay = fill_overlay[:3] + (0,)
        overlay = Image.new("RGBA", canvas.size, cast(RGBA, fill_overlay))
        await self._paste_image(color, mask=mask, canvas=overlay)
        # Paste the overlay onto the canvas
        await self._loop.run_in_executor(self.__executor, canvas.alpha_composite, overlay)

    async def _tint_image(self, im: Image.Image, color: RGB) -> Image.Image:
        alpha = im.split()[3]
        gray = await self._loop.run_in_executor(self.__executor, ImageOps.grayscale, im)
        result = await self._loop.run_in_executor(self.__executor, ImageOps.colorize, gray, color, color)  # type: ignore
        await self._loop.run_in_executor(self.__executor, result.putalpha, alpha)
        return result

    async def _set_transparency(self, im: Image.Image, factor: int) -> Image.Image:
        """Add transparency to an image.

        Parameters
        ----------
        im: :class:`PIL.Image.Image`
            The image to add transparency to.
        factor: :class:`int`
            The alpha value to add to the image.
        """

        # TODO: Improve speed and performance
        def _process(im: Image.Image, factor: int):
            in_img = im.convert("RGBA")
            out_img = Image.new("RGBA", in_img.size, (0, 0, 0, 0))
            for x in range(in_img.width):
                for y in range(in_img.height):
                    r, g, b, a = in_img.getpixel((x, y))
                    if a > 0:
                        new_alpha = max(a - factor, 0)
                        out_img.putpixel((x, y), (r, g, b, new_alpha))
            return out_img

        return await self._loop.run_in_executor(self.__executor, _process, im, factor)

    async def _set_transparency_fast(self, im: Image.Image, factor: float):
        """(Fast) Add transparency to an image.

        Parameters
        ----------
        im: :class:`PIL.Image.Image`
            The image to add transparency to.
        factor: :class:`float`
            The brightness value to adjust the image by.
        """

        # Separate the alpha channel
        alpha = im.split()[3]

        # Adjust the alpha channel according to the factor, use brightness
        alpha = await AsyncImageEnhance.process(alpha, factor, subclass=ImageEnhance.Brightness)
        # Paste the alpha channel back into the image
        await self._loop.run_in_executor(self.__executor, im.putalpha, alpha)

    async def _paste_image(
        self,
        img: Image.Image | RGB | RGBA,
        box: tuple[float, float] | tuple[float, float, float, float] | None = None,
        mask: Image.Image | None = None,
        *,
        canvas: Image.Image | None = None,
    ) -> None:
        """Paste an image onto the canvas.

        Parameters
        ----------
        img: :class:`PIL.Image.Image` | :class:`tuple[int, int, int]`
            The image or color to paste.
        box: :class:`tuple[float, float]` | :class:`tuple[float, float, float, float]` | None, optional
            The box boundary to paste. (top-left, bottom-right) or (top-left, top-right, bottom-left, bottom-right).
        mask: :class:`PIL.Image.Image` | None, optional
            The mask to use, by default None
        canvas: :class:`PIL.Image.Image` | None, optional
            The canvas to draw on, defaults to the current canvas.

        Raises
        ------
        :class:`RuntimeError`
            Canvas is not initialized, and no canvas is provided.
        """

        if not self.has_canvas() and canvas is None:
            raise RuntimeError("Canvas is not initialized, and no canvas is provided.")
        canvas = canvas or self._canvas
        await self._loop.run_in_executor(self.__executor, canvas.paste, img, box, mask)  # type: ignore

    async def _crop_image(self, img: Image.Image, box: tuple[float, float, float, float]) -> Image.Image:
        """Crop an image.

        Parameters
        ----------
        img: :class:`PIL.Image.Image`
            The image to crop.
        box: :class:`tuple[float, float, float, float]`
            The box boundary to crop. (top-left, bottom-right)

        Returns
        -------
        :class:`PIL.Image.Image`
            The cropped image.

        """

        return await self._loop.run_in_executor(self.__executor, img.crop, box)  # type: ignore

    async def _resize_image(
        self, img: Image.Image, size: tuple[int, int], resampling: Image.Resampling | None = None
    ) -> Image.Image:
        """Resize an image.

        Parameters
        ----------
        img: :class:`PIL.Image.Image`
            The image to resize.
        box: :class:`tuple[float, float, float, float]`
            The box boundary to crop. (top-left, bottom-right)
        resampling: :class:`PIL.Image.Resampling`, optional
            The resampling method to use when resizing the mask.
            If not provided, will use the default resampling method

        Returns
        -------
        :class:`PIL.Image.Image`
            The cropped image.
        """

        return await self._loop.run_in_executor(self.__executor, img.resize, size, resampling)

    async def _resize_image_side(
        self,
        img: Image.Image,
        target: int,
        side: Literal["h", "w", "height", "width"] = "w",
        resampling: Image.Resampling | None = None,
    ):
        """Resize an image side according to the target size.

        Parameters
        ----------
        img: :class:`PIL.Image.Image`
            The image to resize.
        target: :class:`int`
            The target size.
        side: :class:`Literal["h", "w"]`, optional
            Width or height, by default "w".
            This will be used to determine which side to resize, the unprovided side will be resized
            according to the aspect ratio of the image.
        resampling: :class:`PIL.Image.Resampling`, optional
            The resampling method to use when resizing the mask.
            If not provided, will use the default resampling method

        Returns
        -------
        :class:`PIL.Image.Image`
            The cropped image.
        """

        match side.lower()[0]:
            case "h":
                height = target
                width = round(height / img.height * img.width)
            case _:
                width = target
                height = round(width / img.width * img.height)

        return await self._loop.run_in_executor(self.__executor, img.resize, (width, height), resampling)

    async def _point_image(
        self, img: Image.Image, handler: Image.ImagePointHandler | Callable[[int | float], int | float]
    ) -> Image.Image:
        """Point process an image.

        Parameters
        ----------
        img: :class:`PIL.Image.Image`
            The image to point process.
        handler: :class:`PIL.Image.ImagePointHandler` | :class:`Callable[[int | float], int | float]`
            The handler to use.

        Returns
        -------
        :class:`PIL.Image.Image`
            The point processed image.
        """

        def _process(img: Image.Image, handler: Image.ImagePointHandler | Callable[[int | float], int | float]):
            return img.point(handler)

        return await self._loop.run_in_executor(self.__executor, _process, img, handler)

    async def _async_open(self, img_path: AsyncPath) -> Image.Image:
        """Open an image asynchronously.

        Parameters
        ----------
        img_path: :class:`AsyncPath`
            The image path.

        Returns
        -------
        :class:`PIL.Image.Image`
            The opened image.

        Raises
        ------
        :class:`FileNotFoundError`
            The file is not found.
        :class:`PIL.UnidentifiedImageError`
            The file is not a valid image.
        """

        return await self._img_cache.get(img_path)

    async def _async_save_bytes(self, canvas: Image.Image) -> BytesIO:
        """Save the canvas as :class:`BytesIO` asynchronously.

        Parameters
        ----------
        canvas: :class:`PIL.Image.Image`
            The canvas to save.

        Returns
        -------
        :class:`BytesIO`
            The saved canvas.
        """

        io = BytesIO()
        await self._loop.run_in_executor(self.__executor, canvas.save, io, "PNG")
        io.seek(0)
        return io

    async def _async_close(self, canvas: Image.Image) -> None:
        """Close the canvas asynchronously.

        Parameters
        ----------
        canvas: :class:`PIL.Image.Image`
            The canvas to close.
        """

        return await self._img_cache.close(canvas)

    def format_timestamp(self, timestamp: datetime) -> str:
        """Format a timestamp.

        Parameters
        ----------
        timestamp: :class:`datetime.datetime`
            The timestamp to format.

        Returns
        -------
        :class:`str`
            The formatted timestamp.
        """

        # If Naive, assume UTC
        if timestamp.tzinfo is None or timestamp.tzinfo.utcoffset(timestamp) is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        locale = get_babel_locale(self._language)
        mdy = format_date(timestamp, locale=locale)
        dow = format_date(timestamp, locale=locale, format="EE")
        hm = format_time(timestamp, locale=locale, format="HH:mm:ss ZZZZ")

        return f"{dow}, {mdy} {hm}"

    def format_number(self, number: int | float, percent: bool = False, /, *, comma: bool = False) -> str:
        """Format a number.

        Parameters
        ----------
        number: :class:`int` | :class:`float`
            The number to format.

        Returns
        -------
        :class:`str`
            The formatted number.
        """

        locale = get_babel_locale(self._language)

        if not percent:
            if comma:
                return format_decimal(round(number), locale=locale, decimal_quantization=True)
            return str(round(number))

        # Percentage format
        pct_fmt = "#,###.#%" if comma else "#.#%"
        return format_percent(number, locale=locale, format=pct_fmt)

    async def create(self, **kwargs: Any) -> bytes:
        """
        Create the card.
        """

        raise NotImplementedError

    async def close(self, clear_all: bool = True, /) -> None:
        """
        Close all the images.

        Parameters
        ----------
        clear_all: :class:`bool`, optional
            Whether to clear all the images, by default True
        """

        if self._canvas is not None and not isinstance(self._canvas.im, DeferredError):
            await self._async_close(self._canvas)
        if clear_all:
            await self._img_cache.clear()

    def shutdown_thread(self):
        self.__executor.shutdown()
