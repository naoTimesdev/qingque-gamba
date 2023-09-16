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

# Relic scoring system
# Version 0.1, 2023/09/16

from __future__ import annotations

from pathlib import Path
from typing import Literal, TypeAlias, cast

import msgspec
import orjson
from aiopath import AsyncPath
from msgspec import Struct, field

from qingque.mihomo.models.characters import Character
from qingque.starrail.loader import SRSDataLoader
from qingque.starrail.models.relics import SRSRelicType

__all__ = (
    "RelicScoring",
    "RelicScores",
    "RelicScoreValue",
)
StatType: TypeAlias = str
CharId: TypeAlias = str
RelicRatio: TypeAlias = dict[StatType, float]
StatRank = Literal["SS", "S", "A", "B", "C", "D", "F"]


class RelicItemWeight(Struct, frozen=True):
    head: RelicRatio = field(name="1")
    hand: RelicRatio = field(name="2")
    body: RelicRatio = field(name="3")
    foot: RelicRatio = field(name="4")
    planar_orb: RelicRatio = field(name="5")
    planar_rope: RelicRatio = field(name="6")

    def get(self, relic_type: SRSRelicType, /) -> RelicRatio:
        match relic_type:
            case SRSRelicType.Head:
                return self.head
            case SRSRelicType.Hand:
                return self.hand
            case SRSRelicType.Body:
                return self.body
            case SRSRelicType.Foot:
                return self.foot
            case SRSRelicType.PlanarOrb:
                return self.planar_orb
            case SRSRelicType.PlanarRope:
                return self.planar_rope


class RelicWeight(Struct, frozen=True):
    stats: RelicItemWeight = field(name="main")
    """:class:`RelicItemWeight`: The weight of the stats."""
    weights: dict[StatType, float] = field(name="weight")
    """:class:`dict[StatType, float]`: The weight of how each stats should be calculated."""
    max: float
    """:class:`float`: The maximum value of the character stats possible."""
    sets: list[str] = field(default_factory=list)
    """:class:`list[str]`: The relic sets that the character is using."""


class RelicScoreValue(Struct, frozen=True):
    id: str
    """:class:`str`: The ID of the relic."""
    value: str
    """:class:`str`: The value of the relic."""
    rank: StatRank
    """:class:`StatRank`: The rank of the relic."""


class RelicScores(Struct, frozen=True):
    scores: dict[str, RelicScoreValue]
    """:class:`dict[str, RelicScoreValue]`: The scores for each relic ID."""
    max: float
    """:class:`float`: The maximum value of the character stats possible."""
    rank: StatRank
    """:class:`StatRank`: The overall rank of the character."""


class RelicScoring:
    def __init__(self, score_sheets: AsyncPath | Path, /) -> None:
        self._score_sheets = AsyncPath(score_sheets) if isinstance(score_sheets, Path) else score_sheets

        # Actual meta scoring
        self._score_meta: dict[CharId, RelicWeight] = {}

    def _load_models(self, bytes_data: bytes) -> None:
        score_json = orjson.loads(bytes_data)
        for char_id, score_raw in score_json.items():
            loaded_model = msgspec.json.decode(orjson.dumps(score_raw), type=RelicWeight)
            self._score_meta[char_id] = loaded_model

    async def async_load(self) -> None:
        self.unload()
        async with self._score_sheets.open("rb") as f:
            score_bytes = await f.read()
            self._load_models(cast(bytes, score_bytes))

    def load(self) -> None:
        # Open as Path
        self.unload()
        ppath = Path(self._score_sheets)
        with ppath.open("rb") as f:
            score_bytes = f.read()
            self._load_models(score_bytes)

    def unload(self):
        self._score_meta.clear()
        self._max_values = 0.0

    def empty(self) -> bool:
        return not bool(self._score_meta)

    def _get_rank(self, score: float, max_score: float, /) -> StatRank:
        ratio = score / 10
        if ratio >= 0.95:
            return "SS"
        elif ratio >= 0.85:
            return "S"
        elif ratio >= 0.75:
            return "A"
        elif ratio >= 0.6:
            return "B"
        elif ratio >= 0.4:
            return "C"
        elif ratio >= 0.2:
            return "D"
        else:
            return "F"

    def calculate(self, character: Character, /, *, loader: SRSDataLoader) -> RelicScores:
        scoring = self._score_meta.get(character.id)
        if scoring is None:
            raise KeyError(f"Character <{character.name} {character.id}> is not found in the scoring system.")

        # Calcualte substats
        relic_score_all: dict[str, float] = {}
        for relic in character.relics:
            item_score = 0.0
            relic_info = loader.relics[relic.id]
            relic_type = relic_info.type
            for substat in relic.sub_stats:
                item_score += scoring.weights.get(substat.type, 0) * (substat.count + 0.25 * substat.step)
            main_eff = scoring.stats.get(relic_type).get(relic.main_stats.type, 0)
            item_score = item_score / scoring.max * 0.5 + main_eff * ((relic.level + 1) / 16) * 0.5 + 0.01
            relic_score_all[relic.id] = item_score * 10

        # Sum all the scores
        relic_score_sum = sum(relic_score_all.values()) / 6
        # Make the rank of each relic
        relic_rank_all: dict[str, RelicScoreValue] = {}
        for relic_id, relic_score in relic_score_all.items():
            relic_rank_all[relic_id] = RelicScoreValue(
                id=relic_id, value=str(relic_score), rank=self._get_rank(relic_score, scoring.max)
            )

        # Calculate the overall rank
        overall_rank = self._get_rank(relic_score_sum, scoring.max)
        return RelicScores(scores=relic_rank_all, max=scoring.max, rank=overall_rank)
