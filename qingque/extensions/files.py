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

import io
import os
from typing import Any

from discord import File
from discord.utils import MISSING


def _strip_spoiler(filename: str) -> tuple[str, bool]:
    stripped = filename
    while stripped.startswith("SPOILER_"):
        stripped = stripped[8:]  # len('SPOILER_')
    spoiler = stripped != filename
    return stripped, spoiler


class FileBytes(File):
    def __init__(
        self,
        fp: str | bytes | os.PathLike[Any] | io.BufferedIOBase,
        filename: str | None = None,
        *,
        spoiler: bool = MISSING,
        description: str | None = None,
    ):
        if filename is None:
            filename = "untitled"
        if isinstance(fp, bytes):
            self._bytes_data = fp
        elif isinstance(fp, str):
            self._bytes_data = fp.encode("utf-8")
        elif isinstance(fp, io.IOBase):
            if not (fp.seekable() and fp.readable()):
                raise ValueError("File buffer must be seekable and readable")
            # Reset the file to the beginning
            fp.seek(0)
            self._bytes_data = fp.read()
            fp.close()
        else:
            raise TypeError("fp must be str, bytes, or os.PathLike")

        self._filename, filename_spoiler = _strip_spoiler(filename)

        if spoiler is MISSING:
            spoiler = filename_spoiler

        self.spoiler: bool = spoiler
        self.description: str | None = description

        self._fp = io.BytesIO(self._bytes_data)

    def reset(self, *, seek: int | bool = True) -> None:
        if seek:
            self._fp.seek(0)

    def close(self) -> None:
        self._fp.close()

    @property
    def fp(self) -> io.BytesIO:
        """:class:`io.BytesIO`: The internal file pointer."""
        if self._fp.closed:
            # Closed? Let's reopen it
            self._fp = io.BytesIO(self._bytes_data)
        return self._fp
