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

# A collection of asynchronous version of PIL class/methods.

from __future__ import annotations

import asyncio
from typing import Protocol

from PIL import Image
from PIL.ImageFilter import Filter as _SyncFilter

__all__ = (
    "AsyncImageEnhance",
    "AsyncImageFilter",
)


class _SyncEnhance(Protocol):
    """A protocol for the enhance class, a recreated version of :class:`PIL.ImageEnhance._Enhance`."""

    def __init__(self, image: Image.Image) -> None:
        ...

    def enhance(self, factor: float) -> Image.Image:
        ...


class AsyncImageEnhance:
    __slots__ = (
        "_enhancer",
        "_loop",
    )

    def __init__(
        self, image: Image.Image, *, subclass: type[_SyncEnhance], loop: asyncio.AbstractEventLoop | None = None
    ) -> None:
        """Initialize the asynchronous image enhance mechanism.

        Parameters
        ----------
        image: :class:`PIL.Image.Image`
            The image to enhance.
        subclass: :class:`type[PIL.ImageEnhance._Enhance]`
            The subclass of :class:`PIL.ImageEnhance._Enhance` to use.
        loop: :class:`asyncio.AbstractEventLoop | None`, optional
            The event loop to use, by default None
        """

        self._enhancer: _SyncEnhance = subclass(image)
        self._loop: asyncio.AbstractEventLoop = loop or asyncio.get_running_loop()

    async def enhance(self, factor: float) -> Image.Image:
        """Asynchronously enhance the image.

        Parameters
        ----------
        factor: :class:`float`
            The factor to enhance the image.

        Returns
        -------
        :class:`PIL.Image.Image`
            The enhanced image.
        """

        enhanced = await self._loop.run_in_executor(None, self._enhancer.enhance, factor)
        return enhanced

    @classmethod
    async def process(
        cls: type[AsyncImageEnhance],
        image: Image.Image,
        factor: float,
        *,
        subclass: type[_SyncEnhance],
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> Image.Image:
        """Asynchronously process the image.

        Parameters
        ----------
        image: :class:`PIL.Image.Image`
            The image to enhance.
        factor: :class:`float`
            The factor to enhance the image.
        subclass: :class:`type[PIL.ImageEnhance._Enhance]`
            The subclass of :class:`PIL.ImageEnhance._Enhance` to use.
        loop: :class:`asyncio.AbstractEventLoop | None`, optional
            The event loop to use, by default None

        Returns
        -------
        :class:`PIL.Image.Image`
            The enhanced image.
        """

        return await cls(image, subclass=subclass, loop=loop).enhance(factor)


class AsyncImageFilter:
    __slots__ = (
        "_filterer",
        "_loop",
    )

    def __init__(self, *, subclass: _SyncFilter, loop: asyncio.AbstractEventLoop | None = None) -> None:
        """Initialize the asynchronous image filter mechanism.

        Parameters
        ----------
        subclass: :class:`PIL.ImageFilter.Filter`
            The subclass of :class:`PIL.ImageFilter.Filter` to use.
            Must have the :meth:`PIL.ImageFilter.Filter.filter` method.
        loop: :class:`asyncio.AbstractEventLoop | None`, optional
            The event loop to use, by default None
        """

        self._filterer: _SyncFilter = subclass
        if not isinstance(subclass, _SyncFilter):
            raise TypeError(f"{subclass.__class__.__name__} must be a subclass of PIL.ImageFilter.Filter.")
        # Check if the subclass has the filter method.
        self._loop: asyncio.AbstractEventLoop = loop or asyncio.get_running_loop()

    async def filter(self, image: Image.Image) -> Image.Image:
        """Asynchronously filter the image.

        Parameters
        ----------
        image: :class:`PIL.Image.Image`
            The image to filter.

        Returns
        -------
        :class:`PIL.Image.Image`
            The filtered image.
        """

        filtered = await self._loop.run_in_executor(None, image.filter, self._filterer)
        return filtered

    @classmethod
    async def process(
        cls: type[AsyncImageFilter],
        image: Image.Image,
        *,
        subclass: _SyncFilter,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> Image.Image:
        """Asynchronously process the image.

        Parameters
        ----------
        image: :class:`PIL.Image.Image`
            The image to filter.
        subclass: :class:`PIL.ImageFilter.Filter`
            The subclass of :class:`PIL.ImageFilter.Filter` to use.
            Must have the :meth:`PIL.ImageFilter.Filter.filter` method.
        loop: :class:`asyncio.AbstractEventLoop | None`, optional
            The event loop to use, by default None

        Returns
        -------
        :class:`PIL.Image.Image`
            The filtered image.
        """

        return await cls(subclass=subclass, loop=loop).filter(image)
