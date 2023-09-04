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

import logging
from enum import Enum
from string import Formatter
from typing import Any, cast

import orjson
from discord import Locale

from qingque.mihomo.models.constants import MihomoLanguage
from qingque.utils import complex_walk

__all__ = (
    "QingqueLanguage",
    "QingqueI18n",
    "get_i18n",
    "load_i18n_languages",
)

logger = logging.getLogger("qingque.i18n")


class QingqueLanguage(str, Enum):
    CHT = "zh-TW"
    CHS = "zh-CN"
    DE = "de-DE"
    EN = "en-US"
    ES = "es-ES"
    FR = "fr-FR"
    ID = "id-ID"
    JP = "ja-JP"
    KR = "ko-KR"
    PT = "pt-PT"
    RU = "ru-RU"
    TH = "th-TH"
    VI = "vi-VN"

    def to_mihomo(self) -> MihomoLanguage:
        name = self.name.lower()
        if name == "chs":
            name = "cn"
        if name == "it":
            name = "en"
        return MihomoLanguage(name)

    @classmethod
    def from_mihomo(cls: type[QingqueLanguage], lang: MihomoLanguage):
        match lang:
            case MihomoLanguage.CHT:
                return cls.CHT
            case MihomoLanguage.CHS:
                return cls.CHS
            case MihomoLanguage.DE:
                return cls.DE
            case MihomoLanguage.EN:
                return cls.EN
            case MihomoLanguage.ES:
                return cls.ES
            case MihomoLanguage.FR:
                return cls.FR
            case MihomoLanguage.ID:
                return cls.ID
            case MihomoLanguage.JP:
                return cls.JP
            case MihomoLanguage.KR:
                return cls.KR
            case MihomoLanguage.PT:
                return cls.PT
            case MihomoLanguage.RU:
                return cls.RU
            case MihomoLanguage.TH:
                return cls.TH
            case MihomoLanguage.VI:
                return cls.VI
            case _:
                raise ValueError(f"Unknown language {lang!r}.")

    @classmethod
    def from_discord(cls: type[QingqueLanguage], lang: Locale):
        match lang:
            case Locale.american_english | Locale.british_english:
                return cls.EN
            case Locale.chinese:
                return cls.CHS
            case Locale.taiwan_chinese:
                return cls.CHT
            case Locale.german:
                return cls.DE
            case Locale.french:
                return cls.FR
            case Locale.indonesian:
                return cls.ID
            case Locale.brazil_portuguese:
                return cls.PT
            case Locale.russian:
                return cls.RU
            case Locale.japanese:
                return cls.JP
            case Locale.korean:
                return cls.KR
            case Locale.thai:
                return cls.TH
            case Locale.vietnamese:
                return cls.VI
            case Locale.spain_spanish:
                return cls.ES
            case _:
                return cls.EN


KVI18n = dict[str, str]
KVI18nDict = dict[str, KVI18n | str]


class _OptinalDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


class OptionalFormatter:
    def __init__(self, data: dict[str, Any]) -> None:
        self.fmt = Formatter()
        self.data = _OptinalDict(data)

    @classmethod
    def format(cls, text: str, *args: Any, **kwargs: Any):
        formatter = cls(kwargs)
        return formatter.fmt.vformat(text, args, formatter.data)


class QingqueI18n:
    _DEFAULT = QingqueLanguage.EN
    _LOCALES_DATA: dict[QingqueLanguage, KVI18nDict]

    def __init__(self) -> None:
        self._LOCALES_DATA = {}

    def _get_from_lang(self, key: str, language: QingqueLanguage | str) -> str | None:
        if isinstance(language, str):
            language = QingqueLanguage(language)
        if language not in self._LOCALES_DATA:
            return None
        locale = self._LOCALES_DATA[language]
        translation = complex_walk(locale, key)
        return cast(str | None, translation)

    def _fmt_tl(self, text: str, params: list[str] | dict[str, str] | None = None) -> str:
        if params is not None:
            if isinstance(params, list):
                return OptionalFormatter.format(text, *params)
            return OptionalFormatter.format(text, **params)
        return text

    def t(
        self,
        key: str,
        params: list[str] | dict[str, str] | None = None,
        *,
        language: QingqueLanguage | str | None = None,
    ) -> str:
        language = language or self._DEFAULT
        translation = self._get_from_lang(key, language)
        if translation is None:
            logger.debug(f"Translation for {key} in {language} is not found, fallback to {self._DEFAULT.name}")
            translation = self._get_from_lang(key, self._DEFAULT)
            if translation is None:
                logger.debug(f"Translation for {key} in {self._DEFAULT.name} is not found, fallback to raw key")
                return key

        return self._fmt_tl(translation, params)

    def load(self, language: QingqueLanguage, data: KVI18nDict):
        # Merge the data
        self._LOCALES_DATA.setdefault(language, {}).update(data)

    def copy(self, default: QingqueLanguage | None = None) -> QingqueI18n:
        new = QingqueI18n()
        new._LOCALES_DATA = self._LOCALES_DATA.copy()
        new._DEFAULT = default or self._DEFAULT
        return new


_QINGQUE_I18N = QingqueI18n()
_LANGUAGE_LOADED = False


def get_i18n() -> QingqueI18n:
    global _QINGQUE_I18N, _LANGUAGE_LOADED

    if not _LANGUAGE_LOADED:
        load_i18n_languages()

    return _QINGQUE_I18N


def load_i18n_languages():
    global _LANGUAGE_LOADED, _QINGQUE_I18N

    from pathlib import Path

    root_dir = Path(__file__).absolute().parent.parent
    languages_dir = root_dir / "i18n"

    for language_dir in languages_dir.iterdir():
        if not language_dir.is_dir():
            continue
        language = QingqueLanguage(language_dir.stem)
        logger.debug(f"Loading language {language.name}...")
        for file in language_dir.iterdir():
            if file.suffix in [".json", "json"]:
                logger.debug(f"-- Loading file {file.name}...")
                json_data = orjson.loads(file.read_bytes())
                _QINGQUE_I18N.load(language, cast(KVI18nDict, json_data))

    _LANGUAGE_LOADED = True
