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
import logging
from pathlib import Path
from zipfile import ZipFile

import aiohttp
from aiopath import AsyncPath

__all__ = (
    "get_march7th_latest_commit",
    "download_commit_archive",
)
CURRENT_PATH = Path(__file__).absolute().parent
logger = logging.getLogger("qingque.march7th")
CHUNK_SIZE = 1 * 1024 * 1024  # 1MB
REPO_URL = "https://s3.eu-central-1.wasabisys.com/nao-archive/SRS"
API_FETCH_URL = "https://s3.eu-central-1.wasabisys.com/nao-archive/SRS/commit.index"


async def delete_directory_contents(file_or_dir: AsyncPath):
    if not await file_or_dir.is_dir():
        return

    async for child in file_or_dir.iterdir():
        if await child.is_dir():
            await delete_directory_contents(child)
            await child.rmdir()
        else:
            await child.unlink()


async def download_commit_archive(commit_id: str, *, client: aiohttp.ClientSession | None = None):
    loop = asyncio.get_running_loop()
    ASSETS_FOLDER = AsyncPath(CURRENT_PATH / "assets" / "srs")  # type: ignore
    client = client or aiohttp.ClientSession()

    ZIP_PATH = ASSETS_FOLDER / "StarRailRes.zip"

    # https://github.com/Mar-7th/StarRailRes/archive/36f180c2ad54c454d8f4fe5c461a811bda89bf37.zip
    archive_url = f"{REPO_URL}/{commit_id}.zip"

    logger.info(f"Downloading {archive_url}...")
    timeout = aiohttp.ClientTimeout(sock_connect=10, sock_read=60, connect=10, total=60)
    async with client.get(archive_url, timeout=timeout) as resp:
        # Chunk downloading so it does not eat up memory
        async with ZIP_PATH.open("wb") as fp:
            async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                await fp.write(chunk)

    logger.info("Extracting contents...")

    zip_file = await loop.run_in_executor(None, ZipFile, Path(ZIP_PATH))
    zip_contents = await loop.run_in_executor(None, zip_file.infolist)

    for content in zip_contents:
        filename = content.filename

        has_suffix = Path(filename).suffix != ""
        if not has_suffix:
            continue

        target_path = ASSETS_FOLDER / filename
        await target_path.parent.mkdir(parents=True, exist_ok=True)

        # Read the file from the zip
        read_content = await loop.run_in_executor(None, zip_file.read, content)
        await target_path.write_bytes(read_content)

    logger.info("Done extracting contents, cleaning up...")
    # Close the zip file
    await loop.run_in_executor(None, zip_file.close)
    # Delete the zip file
    await ZIP_PATH.unlink()
    logger.info(f"Success! Dataset updated to {commit_id}")


async def get_march7th_latest_commit(*, client: aiohttp.ClientSession | None = None):
    ASSETS_FOLDER = AsyncPath(CURRENT_PATH / "assets" / "srs")  # type: ignore
    await ASSETS_FOLDER.mkdir(parents=True, exist_ok=True)

    commit_index = ASSETS_FOLDER / ".." / "commit.index"
    index_file = ""
    if await commit_index.exists():
        index_file = (await commit_index.read_text()).strip()

    client = client or aiohttp.ClientSession()
    async with client.get(API_FETCH_URL) as resp:
        resp.raise_for_status()
        sha_commit = await resp.text()

    if sha_commit != index_file:
        logger.info("There is a new commit available, downloading...")
        for direct in ["icon", "image", "index"]:
            await delete_directory_contents(ASSETS_FOLDER / direct)
        # Rewrite the index file
        await commit_index.write_text(index_file)
        await download_commit_archive(sha_commit, client=client)

        await commit_index.write_text(sha_commit)
    else:
        logger.info("No new commit available, skipping...")
