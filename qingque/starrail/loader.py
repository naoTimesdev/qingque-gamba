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

import gc
from pathlib import Path
from typing import TypeVar, overload

import msgspec
import orjson
from aiopath import AsyncPath
from msgspec import Struct

from qingque.i18n import QingqueLanguage
from qingque.mihomo.models.constants import MihomoLanguage
from qingque.tooling import get_logger

from .models import (
    SRSAchievement,
    SRSAvatar,
    SRSCharacter,
    SRSCharacterEidolon,
    SRSCharacterSkill,
    SRSCharacterSkillTrace,
    SRSDescription,
    SRSElement,
    SRSItem,
    SRSLightCone,
    SRSLightConeSuperimpose,
    SRSNickname,
    SRSPath,
    SRSPromotion,
    SRSProperties,
    SRSRelic,
    SRSRelicSet,
    SRSRelicStats,
    SRSRelicSubStats,
    SRSRogueBlessing,
    SRSRogueBlessingType,
    SRSRogueCurio,
    SRSRogueDLCBlock,
    SRSRogueWorld,
)

__all__ = ("SRSDataLoader",)
logger = get_logger("qingque.starrail.loader")
INDEX_ROOT_DIR = Path(__file__).absolute().parent.parent / "assets" / "srs" / "index"

SRSModelT = TypeVar("SRSModelT", bound=Struct)
KVModel = dict[str, SRSModelT]


class SRSDataLoader:
    def __init__(self, language: MihomoLanguage, *, base_path: Path | None = None) -> None:
        self._language: MihomoLanguage = language
        self.base_path: Path = base_path or INDEX_ROOT_DIR

        # Attributes
        self._achievements: KVModel[SRSAchievement] | None = None
        self._avatars: KVModel[SRSAvatar] | None = None
        self._characters_eidolons: KVModel[SRSCharacterEidolon] | None = None
        self._characters_promotions: KVModel[SRSPromotion] | None = None
        self._characters_skills: KVModel[SRSCharacterSkill] | None = None
        self._characters_skills_traces: KVModel[SRSCharacterSkillTrace] | None = None
        self._characters: KVModel[SRSCharacter] | None = None
        self._descriptions: KVModel[SRSDescription] | None = None
        self._elements: KVModel[SRSElement] | None = None
        self._items: KVModel[SRSItem] | None = None
        self._light_cones: KVModel[SRSLightCone] | None = None
        self._light_cones_superimposes: KVModel[SRSLightConeSuperimpose] | None = None
        self._light_cones_promotions: KVModel[SRSPromotion] | None = None
        self._nicknames: SRSNickname | None = None
        self._paths: KVModel[SRSPath] | None = None
        self._properties: KVModel[SRSProperties] | None = None
        self._relics: KVModel[SRSRelic] | None = None
        self._relics_stats: KVModel[SRSRelicStats] | None = None
        self._relics_sub_stats: KVModel[SRSRelicSubStats] | None = None
        self._relics_sets: KVModel[SRSRelicSet] | None = None
        self._rogues: KVModel[SRSRogueWorld] | None = None
        self._rogue_curios: KVModel[SRSRogueCurio] | None = None
        self._rogue_blessings: KVModel[SRSRogueBlessing] | None = None
        self._rogue_blessing_types: KVModel[SRSRogueBlessingType] | None = None
        self._rogue_dlc_blocks: KVModel[SRSRogueDLCBlock] | None = None

        self.__loader_maps: dict[str, tuple[type[Struct], str]] = {
            "achievements": (SRSAchievement, "_achievements"),
            "avatars": (SRSAvatar, "_avatars"),
            "character_ranks": (SRSCharacterEidolon, "_characters_eidolons"),
            "character_promotions": (SRSPromotion, "_characters_promotions"),
            "character_skills": (SRSCharacterSkill, "_characters_skills"),
            "character_skill_trees": (SRSCharacterSkillTrace, "_characters_skills_traces"),
            "characters": (SRSCharacter, "_characters"),
            "descriptions": (SRSDescription, "_descriptions"),
            "elements": (SRSElement, "_elements"),
            "items": (SRSItem, "_items"),
            "light_cones": (SRSLightCone, "_light_cones"),
            "light_cone_ranks": (SRSLightConeSuperimpose, "_light_cones_superimposes"),
            "light_cone_promotions": (SRSPromotion, "_light_cones_promotions"),
            # "nicknames": (SRSNickname, '_nicknames'),
            "paths": (SRSPath, "_paths"),
            "properties": (SRSProperties, "_properties"),
            "relics": (SRSRelic, "_relics"),
            "relic_main_affixes": (SRSRelicStats, "_relics_stats"),
            "relic_sub_affixes": (SRSRelicSubStats, "_relics_sub_stats"),
            "relic_sets": (SRSRelicSet, "_relics_sets"),
            "rogue": (SRSRogueWorld, "_rogues"),
            "rogue_curios": (SRSRogueCurio, "_rogue_curios"),
            "rogue_blessings": (SRSRogueBlessing, "_rogue_blessings"),
            "rogue_blessing_types": (SRSRogueBlessingType, "_rogue_blessing_types"),
            "rogue_dlc_blocks": (SRSRogueDLCBlock, "_rogue_dlc_blocks"),
        }

    def __repr__(self) -> str:
        loaded = self._achievements is not None
        return f"<SRSDataLoader language={self._language.value!r} loaded={loaded!r}>"

    @property
    def loaded(self) -> bool:
        return self._achievements is not None

    @property
    def language(self) -> MihomoLanguage:
        return self._language

    @language.setter
    def language(self, value: MihomoLanguage | QingqueLanguage) -> None:
        if isinstance(value, QingqueLanguage):
            value = value.to_mihomo()
        self._language = value

    @overload
    def _load_models(self, data: bytes, model: type[SRSModelT]) -> dict[str, SRSModelT]:
        ...

    @overload
    def _load_models(self, data: bytes, model: type[SRSModelT], *, root_mode: bool = True) -> SRSModelT:
        ...

    def _load_models(
        self, data: bytes, model: type[SRSModelT], *, root_mode: bool = False
    ) -> SRSModelT | dict[str, SRSModelT]:
        if root_mode:
            return msgspec.json.decode(data, type=model)

        # Load orjson first
        orjson_data = orjson.loads(data)
        mapped_kv: dict[str, SRSModelT] = {}
        for key, value in orjson_data.items():
            mapped_kv[key] = msgspec.json.decode(orjson.dumps(value), type=model)
        return mapped_kv

    def loads(self):
        for key, (model, attr) in self.__loader_maps.items():
            if getattr(self, attr) is not None:
                continue
            logger.debug(f"Loading `{key}` index for lang {self._language.value!r}")
            index_json = self.base_path / self._language.value / f"{key}.json"
            index_data = index_json.read_bytes()
            try:
                loaded_models = self._load_models(index_data, model)
            except Exception as exc:
                logger.error(f"Failed to load `{key}` index.", exc_info=exc)
                raise exc
            setattr(self, attr, loaded_models)
        nickname = self.base_path / self._language.value / "nickname.json"
        nickname_data = nickname.read_bytes()
        self._nicknames = self._load_models(nickname_data, SRSNickname, root_mode=True)

    async def async_loads(self) -> None:
        for key, (model, attr) in self.__loader_maps.items():
            if getattr(self, attr) is not None:
                continue
            logger.debug(f"Loading `{key}` index for lang {self._language.value!r}")
            index_json = AsyncPath(self.base_path / self._language.value / f"{key}.json")
            index_data = await index_json.read_bytes()
            try:
                loaded_models = self._load_models(index_data, model)
            except Exception as exc:
                logger.error(f"Failed to load `{key}` index.", exc_info=exc)
            setattr(self, attr, loaded_models)
        nickname = AsyncPath(self.base_path / self._language.value / "nickname.json")
        nickname_data = await nickname.read_bytes()
        self._nicknames = self._load_models(nickname_data, SRSNickname, root_mode=True)

    def unloads(self):
        for _, (_, attr) in self.__loader_maps.items():
            setattr(self, attr, None)
        self._nicknames = None
        # Garbage collection
        gc.collect()

    @property
    def achievements(self) -> KVModel[SRSAchievement]:
        if self._achievements is None:
            raise RuntimeError("You must load the data first.")
        return self._achievements

    @property
    def avatars(self) -> KVModel[SRSAvatar]:
        if self._avatars is None:
            raise RuntimeError("You must load the data first.")
        return self._avatars

    @property
    def characters_eidolons(self) -> KVModel[SRSCharacterEidolon]:
        if self._characters_eidolons is None:
            raise RuntimeError("You must load the data first.")
        return self._characters_eidolons

    @property
    def characters_promotions(self) -> KVModel[SRSPromotion]:
        if self._characters_promotions is None:
            raise RuntimeError("You must load the data first.")
        return self._characters_promotions

    @property
    def characters_skills(self) -> KVModel[SRSCharacterSkill]:
        if self._characters_skills is None:
            raise RuntimeError("You must load the data first.")
        return self._characters_skills

    @property
    def characters_skills_traces(self) -> KVModel[SRSCharacterSkillTrace]:
        if self._characters_skills_traces is None:
            raise RuntimeError("You must load the data first.")
        return self._characters_skills_traces

    @property
    def characters(self) -> KVModel[SRSCharacter]:
        if self._characters is None:
            raise RuntimeError("You must load the data first.")
        return self._characters

    @property
    def descriptions(self) -> KVModel[SRSDescription]:
        if self._descriptions is None:
            raise RuntimeError("You must load the data first.")
        return self._descriptions

    @property
    def elements(self) -> KVModel[SRSElement]:
        if self._elements is None:
            raise RuntimeError("You must load the data first.")
        return self._elements

    @property
    def items(self) -> KVModel[SRSItem]:
        if self._items is None:
            raise RuntimeError("You must load the data first.")
        return self._items

    @property
    def light_cones(self) -> KVModel[SRSLightCone]:
        if self._light_cones is None:
            raise RuntimeError("You must load the data first.")
        return self._light_cones

    @property
    def light_cones_superimposes(self) -> KVModel[SRSLightConeSuperimpose]:
        if self._light_cones_superimposes is None:
            raise RuntimeError("You must load the data first.")
        return self._light_cones_superimposes

    @property
    def light_cones_promotions(self) -> KVModel[SRSPromotion]:
        if self._light_cones_promotions is None:
            raise RuntimeError("You must load the data first.")
        return self._light_cones_promotions

    @property
    def nicknames(self) -> SRSNickname:
        if self._nicknames is None:
            raise RuntimeError("You must load the data first.")
        return self._nicknames

    @property
    def paths(self) -> KVModel[SRSPath]:
        if self._paths is None:
            raise RuntimeError("You must load the data first.")
        return self._paths

    @property
    def properties(self) -> KVModel[SRSProperties]:
        if self._properties is None:
            raise RuntimeError("You must load the data first.")
        return self._properties

    @property
    def relics(self) -> KVModel[SRSRelic]:
        if self._relics is None:
            raise RuntimeError("You must load the data first.")
        return self._relics

    @property
    def relics_stats(self) -> KVModel[SRSRelicStats]:
        if self._relics_stats is None:
            raise RuntimeError("You must load the data first.")
        return self._relics_stats

    @property
    def relics_sub_stats(self) -> KVModel[SRSRelicSubStats]:
        if self._relics_sub_stats is None:
            raise RuntimeError("You must load the data first.")
        return self._relics_sub_stats

    @property
    def relics_sets(self) -> KVModel[SRSRelicSet]:
        if self._relics_sets is None:
            raise RuntimeError("You must load the data first.")
        return self._relics_sets

    @property
    def simulated_universes(self) -> KVModel[SRSRogueWorld]:
        if self._rogues is None:
            raise RuntimeError("You must load the data first.")
        return self._rogues

    @property
    def simuniverse_curios(self) -> KVModel[SRSRogueCurio]:
        if self._rogue_curios is None:
            raise RuntimeError("You must load the data first.")
        return self._rogue_curios

    @property
    def simuniverse_blessings(self) -> KVModel[SRSRogueBlessing]:
        if self._rogue_blessings is None:
            raise RuntimeError("You must load the data first.")
        return self._rogue_blessings

    @property
    def simuniverse_blessing_types(self) -> KVModel[SRSRogueBlessingType]:
        if self._rogue_blessing_types is None:
            raise RuntimeError("You must load the data first.")
        return self._rogue_blessing_types

    @property
    def swarmdlc_blocks(self) -> KVModel[SRSRogueDLCBlock]:
        if self._rogue_dlc_blocks is None:
            raise RuntimeError("You must load the data first.")
        return self._rogue_dlc_blocks
