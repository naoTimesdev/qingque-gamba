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

import re
from typing import Any, Callable

__all__ = (
    "get_indexed",
    "complex_walk",
    "strip_unity_rich_text",
    "unity_rich_to_markdown",
)

_UNITY_RT_SIZE = re.compile(r"<size=(?:\d+)>(.+?)</size>")
_UNITY_RT_COLOR = re.compile(r"<color=(?:[#]?[\w\d]+)>(.+?)</color>")
_UNITY_RT_MAT = re.compile(r"<material=(?:[\d+])>(.+?)</material>")


def get_indexed(data: list, n: int) -> Any | None:
    if not data:
        return None
    try:
        return data[n]
    except (ValueError, IndexError):
        return None


def complex_walk(dictionary: dict | list, paths: str) -> list[Any] | dict[Any, Any] | Any | None:
    if not dictionary:
        return None
    expanded_paths = paths.split(".")
    skip_it = False
    for n, path in enumerate(expanded_paths):
        if skip_it:
            skip_it = False
            continue
        if path.isdigit():
            path = int(path)  # type: ignore
        if path == "*" and isinstance(dictionary, list):
            new_concat = []
            next_path = get_indexed(expanded_paths, n + 1)
            if next_path is None:
                return None
            skip_it = True
            for content in dictionary:
                try:
                    new_concat.append(content[next_path])
                except (TypeError, ValueError, IndexError, KeyError, AttributeError):
                    pass
            if len(new_concat) < 1:
                return new_concat
            dictionary = new_concat
            continue
        try:
            dictionary = dictionary[path]  # type: ignore
        except (TypeError, ValueError, IndexError, KeyError, AttributeError):
            return None
    return dictionary


def urich_re(format: str) -> re.Pattern[str]:
    return re.compile(rf"<{format}>(.+?)</{format}>", re.I)


def strip_unity_rich_text(text: str) -> str:
    basic_format = ["b", "i", "unbreak", "s", "u", "lowercase", "uppercase", "smallcaps", "nobr", "sup"]
    for tag in basic_format:
        text = text.replace(f"<{tag}>", "").replace(f"</{tag}>", "")

    complex_formats = [_UNITY_RT_SIZE, _UNITY_RT_COLOR, _UNITY_RT_MAT]
    for tag in complex_formats:
        text = tag.sub(r"\1", text)
    return text


def _unity_rich_lowercase(m: re.Match[str]) -> str:
    return m.group(1).lower()


def _unity_rich_uppercase(m: re.Match[str]) -> str:
    return m.group(1).upper()


def to_superscript(text: str) -> str:
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-=()"
    subtitute = "ᴬᴮᶜᴰᴱᶠᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾQᴿˢᵀᵁⱽᵂˣʸᶻᵃᵇᶜᵈᵉᶠᵍʰᶦʲᵏˡᵐⁿᵒᵖ۹ʳˢᵗᵘᵛʷˣʸᶻ⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾"
    transltable = text.maketrans("".join(normal), "".join(subtitute))
    return text.translate(transltable)


def to_subscript(text: str) -> str:
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-=()"
    subtitute = "ₐ₈CDₑբGₕᵢⱼₖₗₘₙₒₚQᵣₛₜᵤᵥwₓᵧZₐ♭꜀ᑯₑբ₉ₕᵢⱼₖₗₘₙₒₚ૧ᵣₛₜᵤᵥwₓᵧ₂₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎"  # noqa: RUF001
    transltable = text.maketrans("".join(normal), "".join(subtitute))
    return text.translate(transltable)


def to_smallcaps(text: str) -> str:
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-=()"
    subtitute = "ABCDEFGHIJKLMNOPQRSTUVWXYZᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ0123456789+-=()"  # noqa: RUF001
    transltable = text.maketrans("".join(normal), "".join(subtitute))
    return text.translate(transltable)


def unity_rich_to_markdown(text_data: str) -> str:
    # Sorted by priority
    main_format: dict[re.Pattern[str], str | Callable[[re.Match[str]], str]] = {
        urich_re("b"): "**",
        urich_re("i"): "*",
        urich_re("u"): "__",
        urich_re("s"): "~~",
        urich_re("sup"): lambda m: to_superscript(m.group(1)),
        urich_re("smallcaps"): lambda m: to_smallcaps(m.group(1)),
        urich_re("sub"): lambda m: to_subscript(m.group(1)),
        urich_re("lowercase"): _unity_rich_lowercase,
        urich_re("uppercase"): _unity_rich_uppercase,
    }
    strip_format = ["unbreak", "nobr"]
    for tag in strip_format:
        text_data = text_data.replace(f"<{tag}>", "").replace(f"</{tag}>", "")

    complex_formats = [_UNITY_RT_SIZE, _UNITY_RT_COLOR, _UNITY_RT_MAT]
    for tag in complex_formats:
        text_data = tag.sub(r"\1", text_data)

    for formatter, replacer in main_format.items():
        if callable(replacer):
            text_data = formatter.sub(replacer, text_data)
        else:
            text_data = formatter.sub(rf"{replacer}\1{replacer}", text_data)
    return text_data
