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

import glob
import gzip
import inspect
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING, Optional, overload

import coloredlogs

if TYPE_CHECKING:
    from types import ModuleType

__all__ = (
    "RollingFileHandler",
    "setup_logger",
    "get_logger",
)
ROOT_DIR = Path(__file__).absolute().parent
logger = logging.getLogger("qingque.tooling")


class RollingFileHandler(RotatingFileHandler):
    """
    A log file handler that follows the same format as RotatingFileHandler,
    but automatically roll over to the next numbering without needing to worry
    about maximum file count or something.

    At startup, we check the last file in the directory and start from there.
    """

    maxBytes: int  # noqa: N815
    gunzip: bool

    def __init__(
        self,
        filename: os.PathLike,
        mode: str = "a",
        maxBytes: int = 0,  # noqa: N803
        backupCount: int = 0,  # noqa: N803
        encoding: Optional[str] = None,
        delay: bool = False,
        gunzip: bool = True,
    ) -> None:
        self._last_backup_count = 0
        super().__init__(
            filename, mode=mode, maxBytes=maxBytes, backupCount=backupCount, encoding=encoding, delay=delay
        )
        self.maxBytes = maxBytes
        self.backupCount = backupCount
        self.gunzip = gunzip
        self._determine_start_count()

    def _determine_start_count(self):
        all_files = glob.glob(self.baseFilename + "*")  # noqa: PTH207
        if all_files:
            all_files.sort()
            fn = all_files[-1]
            if fn.endswith(".gz"):
                fn = fn[:-3]
            last_digit = fn.split(".")[-1]
            if last_digit.isdigit():
                self._last_backup_count = int(last_digit)

    def doRollover(self) -> None:  # noqa: N802
        if self.stream and not self.stream.closed:
            self.stream.close()
        self._last_backup_count += 1
        next_name = "%s.%d" % (self.baseFilename, self._last_backup_count)
        self.rotate(self.baseFilename, next_name)
        if not self.delay:
            self.stream = self._open()

    def _safe_gunzip(self, source: str, dest: str):
        try:
            with Path(source).open("rb") as sf:
                with gzip.open(dest + ".gz", "wb") as df:
                    for line in sf:
                        df.write(line)
            return True
        except Exception as exc:
            logger.error("Failed to gzip %s: %s", source, str(exc), exc_info=exc)
            return False

    def _safe_rename(self, source: str, dest: str):
        try:
            Path(source).rename(dest)
            return True
        except Exception as exc:
            logger.error("Failed to rename %s to %s: %s", source, dest, str(exc), exc_info=exc)
            return False

    def _safe_remove(self, source: str):
        try:
            Path(source).unlink(missing_ok=True)
            return True
        except Exception as exc:
            logger.error("Failed to remove %s: %s", source, str(exc), exc_info=exc)
            return False

    def rotator(self, source: str, dest: str) -> None:
        # Override the rotator to gzip the file before moving it
        if not Path(source).exists():
            return  # silently fails
        if self.gunzip:
            # Try to gzip the file
            result = self._safe_gunzip(source, dest)
            if result:
                # If successful, delete the original file
                self._safe_remove(source)
            else:
                # If not successful, just rename the file
                self._safe_rename(source, dest)
        else:
            # Just rename the file
            self._safe_rename(source, dest)


def setup_logger(log_path: Path):
    log_path.parent.mkdir(exist_ok=True)

    file_handler = RollingFileHandler(log_path, maxBytes=5_242_880, backupCount=5, encoding="utf-8")
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[file_handler],
        format="[%(asctime)s] - (%(name)s)[%(levelname)s](%(funcName)s): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger()
    coloredlogs.install(
        fmt="[%(asctime)s %(hostname)s][%(levelname)s] (%(name)s[%(process)d]): %(funcName)s: %(message)s",
        level=logging.INFO,
        logger=logger,
        stream=sys.stdout,
    )

    # Set default logging for some modules
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.DEBUG)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("chardet").setLevel(logging.WARNING)
    logging.getLogger("async_rediscache").setLevel(logging.WARNING)

    # Set back to the default of INFO even if asyncio's debug mode is enabled.
    logging.getLogger("asyncio").setLevel(logging.INFO)
    # Remove PIL's debug logging
    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.INFO)

    return logger


def _inspect_module_name() -> tuple[ModuleType | None, str | None]:
    try:
        stack = inspect.stack()[2]
    except Exception:
        return None, None
    # Get class name
    try:
        class_name = stack[0].f_locals["self"].__class__.__name__
    except Exception:
        class_name = None
    return inspect.getmodule(stack[0]), class_name


def _create_log_name() -> str | None:
    mod, cls_name = _inspect_module_name()
    if mod is None:
        return None
    # Get the path
    file_miss = mod.__file__
    if file_miss is None:
        return None
    mod_path = Path(file_miss)
    relative = mod_path.relative_to(ROOT_DIR).as_posix().split("/")
    # Get the name of the module
    actual_name = []
    for name in relative:
        actual_name.append(name.capitalize().replace(".py", ""))
    mod_name = ".".join(actual_name)
    if cls_name:
        mod_name += f".{cls_name}"
    return mod_name


@overload
def get_logger() -> logging.Logger:
    ...


@overload
def get_logger(name: str) -> logging.Logger:
    ...


def get_logger(name: str | None = None):
    inspect_name = _create_log_name()
    if name is not None:
        return logging.getLogger(name)
    return logging.getLogger(inspect_name)
