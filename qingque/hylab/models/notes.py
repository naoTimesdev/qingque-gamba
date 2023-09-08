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

import time
from enum import Enum

from msgspec import Struct, field

__all__ = (
    "ChronicleNoteAssignmentStatus",
    "ChronicleNoteAssignment",
    "ChronicleNotes",
)


class ChronicleNoteAssignmentStatus(str, Enum):
    Ongoing = "Ongoing"
    Finished = "Finished"

    def is_ongoing(self) -> bool:
        return self is ChronicleNoteAssignmentStatus.Ongoing


class ChronicleNoteAssignment(Struct):
    status: ChronicleNoteAssignmentStatus = field(name="status", default=ChronicleNoteAssignmentStatus.Ongoing)
    """:class:`ChronicleNoteAssignmentStatus`: The status of the assignment."""
    time_left: int = field(name="remaining_time", default=0)
    """:class:`int`: The time left in seconds until the assignment is finished."""
    name: str = field(name="name", default="")
    """:class:`str`: The name of the assignment."""
    characters: list[str] = field(name="avatars", default_factory=list)
    """:class:`list[str]`: The list of characters avatar that are assigned to the assignment."""


class ChronicleNotes(Struct):
    stamina: int = field(name="current_stamina", default=0)
    """:class:`int`: The current stamina of the user."""
    max_stamina: int = field(name="max_stamina", default=240)
    """:class:`int`: The maximum stamina of the user."""
    stamina_recover_in: int = field(name="stamina_recover_time", default=0)
    """:class:`int`: The time in seconds until the stamina is fully recovered."""
    reserve_stamina: int = field(name="current_reserve_stamina", default=0)
    """:class:`int`: The current reserve stamina of the user."""
    is_reserve_stamina_full: bool = field(name="is_reserve_stamina_full", default=False)
    """:class:`bool`: Whether the reserve stamina is full or not."""

    assignment: int = field(name="total_expedition_num", default=0)
    """:class:`int`: The total number of assignment ongoing/unclaimed."""
    assignment_max: int = field(name="accepted_epedition_num", default=4)
    """:class:`int`: The maximum number of assignments that can be accepted."""
    assignments: list[ChronicleNoteAssignment] = field(name="expeditions", default_factory=list)
    """:class:`list[ChronicleNoteAssignment]`: The list of assignments."""

    training_score: int = field(name="current_train_score", default=0)
    """:class:`int`: The current training/daily point of the user."""
    training_max_score: int = field(name="max_train_score", default=500)
    """:class:`int`: The maximum training/daily point of the user."""

    simulated_universe_score: int = field(name="current_rogue_score", default=0)
    """:class:`int`: The current simulated universe point of the user."""
    simulated_universe_max_score: int = field(name="max_rogue_score", default=14000)
    """:class:`int`: The maximum simulated universe point of the user."""

    eow_available: int = field(name="weekly_cocoon_cnt", default=3)
    """:class:`int`: The number of availibility left for Echo of War."""
    eow_limit: int = field(name="weekly_cocoon_limit", default=3)
    """:class:`int`: The maximum number of availibility for Echo of War per week."""

    requested_at: float = field(default_factory=time.time)
    """:class:`float`: Used internally to determine when the notes is requested."""

    @property
    def stamina_reset_at(self) -> float:
        """:class:`float`: The UNIX time when the stamina is fully recovered."""
        return self.requested_at + self.stamina_recover_in
