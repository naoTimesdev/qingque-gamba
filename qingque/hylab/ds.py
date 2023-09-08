"""
MIT License

Copyright (c) 2021-present sadru (genshin.py)
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

import secrets
import string
import time
from hashlib import md5
from typing import Any, Mapping

import orjson

from qingque.hylab.models.base import HYLanguage
from qingque.models.region import HYVRegion

from .constants import DS_SALT

__all__ = (
    "generate_dynamic_salt",
    "generate_cn_dynamic_salt",
    "get_ds_headers",
)


def randrange(low: int, high: int) -> int:
    return secrets.randbelow(high - low) + low


def generate_dynamic_salt(salt: str = DS_SALT[HYVRegion.Overseas]) -> str:
    t = int(time.time())
    r = "".join(secrets.choice(string.ascii_letters) for _ in range(6))
    h = md5(f"salt={salt}&t={t}&r={r}".encode()).hexdigest()  # noqa: S324
    return f"{t},{r},{h}"


def generate_cn_dynamic_salt(
    body: Any = None, query: Mapping[str, Any] | None = None, *, salt: str = DS_SALT[HYVRegion.China]
) -> str:
    t = int(time.time())
    r = randrange(100001, 200000)
    b = orjson.dumps(body).decode("utf-8") if body else ""
    q = "&".join(f"{k}={v}" for k, v in sorted(query.items())) if query else ""

    h = md5(f"salt={salt}&t={t}&r={r}&b={b}&q={q}".encode()).hexdigest()  # noqa: S324
    return f"{t},{r},{h}"


def get_ds_headers(
    region: HYVRegion | None = None,
    data: Any | None = None,
    params: Mapping[str, Any] | None = None,
    lang: HYLanguage | None = None,
) -> dict[str, Any]:
    match region:
        case HYVRegion.China:
            return {
                "x-rpc-app_version": "2.11.1",
                "x-rpc-client_type": "5",
                "DS": generate_cn_dynamic_salt(data, params),
            }
        case HYVRegion.Overseas:
            return {
                "x-rpc-app_version": "1.5.0",
                "x-rpc-client_type": "5",
                "x-rpc-language": lang.value if lang else HYLanguage.EN.value,
                "DS": generate_dynamic_salt(),
            }
        case _:
            raise ValueError(f"Invalid region: {region!r}")
