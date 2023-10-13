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
import gc
from io import BytesIO
from typing import Final

from aiopath import AsyncPath
from PIL import Image
from PIL._util import DeferredError

__all__ = ("StarRailImageCache",)
CACHE_IMG_PATH: Final[str] = "_wrapped_path_"


class StarRailImageCache:
    def __init__(self, *, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self._cache: dict[str, Image.Image] = {}
        self._loop = loop or asyncio.get_running_loop()

    async def get(self, path: AsyncPath) -> Image.Image:
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

        abs_path = await path.absolute()
        if (cached_img := self._cache.get(str(abs_path))) is not None and not isinstance(cached_img.im, DeferredError):
            return cached_img

        io = BytesIO()
        read_data = await path.read_bytes()
        io.write(read_data)
        io.seek(0)

        # Open as RGBA
        as_img = await self._loop.run_in_executor(None, Image.open, io)
        as_img = await self._loop.run_in_executor(None, as_img.convert, "RGBA")
        setattr(as_img, CACHE_IMG_PATH, abs_path)

        if not io.closed:
            io.close()
        del io
        del read_data
        gc.collect()
        return as_img

    async def clear(self) -> None:
        """Close all the images."""

        for img in self._cache.values():
            # Close
            await self._loop.run_in_executor(None, img.close)
        self._cache.clear()
        gc.collect()

    async def close(self, canvas: Image.Image) -> None:
        """Close the canvas asynchronously.

        Parameters
        ----------
        canvas: :class:`PIL.Image.Image`
            The canvas to close.
        """

        if (img_path := getattr(canvas, CACHE_IMG_PATH, None)) is not None:
            try:
                del self._cache[str(img_path)]
            except KeyError:
                pass
            gc.collect()

        await self._loop.run_in_executor(None, canvas.close)
        del canvas
        gc.collect()
