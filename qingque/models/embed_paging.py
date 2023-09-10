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

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import discord
from discord.components import SelectOption
from discord.interactions import Interaction
from discord.utils import MISSING

from qingque.i18n import get_i18n_discord

if TYPE_CHECKING:
    from qingque.bot import QingqueClient

__all__ = (
    "EmbedPaginatedView",
    "EmbedPagingSelectView",
    "PagingChoice",
)


class EmbedPaginatedView(discord.ui.View):
    def __init__(
        self,
        embeds: list[discord.Embed],
        user_id: int,
        files: list[discord.File] | None = None,
        *,
        timeout: float | None = 180,
    ):
        super().__init__(timeout=timeout)
        self._embeds: list[discord.Embed] = embeds
        self._files: list[discord.File] | None = files
        self._user_id: int = user_id
        self._page = 1

        if self._files is not None and len(self._files) != len(self._embeds):
            raise ValueError("Embeds and files must have the same length.")

        self.update_buttons(1)

    @property
    def index(self) -> int:
        return self._page - 1

    async def on_timeout(self) -> None:
        self.previous.disabled = True
        self.next.disabled = True
        if hasattr(self, "_message"):
            embed = self._embeds[self.index]
            await self._message.edit(view=None, embed=embed)

    async def interaction_check(self, interaction: Interaction[QingqueClient]) -> bool:
        return interaction.user.id == self._user_id

    def update_buttons(self, current_page: int) -> None:
        total_page = len(self._embeds)
        self._page = current_page
        self.count.label = f"Page {current_page}/{total_page}"
        if total_page == 1:
            self.previous.disabled = True
            self.next.disabled = True
            return

        if current_page == 1:
            self.previous.disabled = True
            self.next.disabled = False
        elif current_page == total_page:
            self.previous.disabled = False
            self.next.disabled = True
        else:
            self.previous.disabled = False
            self.next.disabled = False

    async def _edit(self, interaction: discord.Interaction) -> None:
        send_thing = {
            "embed": self._embeds[self.index],
            "view": self,
        }
        if self._files is not None:
            send_thing["attachments"] = [self._files[self.index]]
        await interaction.response.edit_message(**send_thing)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, disabled=True)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.update_buttons(self._page - 1)
        await self._edit(interaction)

    @discord.ui.button(label="Page 1/1", style=discord.ButtonStyle.secondary, disabled=True)
    async def count(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        pass

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, disabled=True)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.update_buttons(self._page + 1)
        await self._edit(interaction)

    async def start(
        self,
        interaction: discord.Interaction[QingqueClient],
        *,
        message: discord.InteractionMessage | None = None,
    ) -> None:
        self._interaction = interaction
        send_thing = {
            "embed": self._embeds[self.index],
            "view": self,
        }
        if self._files is not None:
            send_thing["attachments"] = [self._files[self.index]]
        if message is None:
            if interaction.response.is_done():
                original = await interaction.original_response()
                self._message = original
            else:
                if "attachments" in send_thing and self._files is not None:
                    # Remove the attachments from the original message, and use "file" instead
                    del send_thing["attachments"]
                    send_thing["file"] = self._files[self.index]
                await interaction.response.send_message(**send_thing)
                self._message = await interaction.original_response()
        else:
            self._message = message
            await message.edit(**send_thing)


@dataclass
class PagingChoice:
    title: str
    embed: discord.Embed
    file: discord.File | None = None
    emoji: str | discord.PartialEmoji | None = None
    id: str = field(default_factory=lambda: str(uuid4()))


class EmbedPagingSelection(discord.ui.Select):
    def __init__(
        self,
        parent: "EmbedPagingSelectView",
        choices: list[PagingChoice],
        *,
        custom_id: str = MISSING,
        placeholder: str | None = None,
        disabled: bool = False,
    ) -> None:
        self._parent_view = parent

        options: list[SelectOption] = []
        for choice in choices:
            opts = SelectOption(
                label=choice.title,
                value=choice.id,
                emoji=choice.emoji,
            )
            options.append(opts)
        self._choices = choices

        super().__init__(custom_id=custom_id, placeholder=placeholder, disabled=disabled, options=options)

    async def callback(self, inter: discord.Interaction[QingqueClient]):
        sel_choice = self.values[0]
        for choice in self._choices:
            if choice.id == sel_choice:
                await self._parent_view.set_response(inter, choice)
                break


class EmbedPagingSelectView(discord.ui.View):
    _message: discord.InteractionMessage

    def __init__(self, choices: list[PagingChoice], locale: discord.Locale, *, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        t = get_i18n_discord(locale)
        placeholder = t("srchoices.placeholder")

        item = EmbedPagingSelection(self, choices, placeholder=placeholder)
        self._choices: list[PagingChoice] = choices
        self._selection = item
        self.add_item(item)

    async def set_response(self, inter: discord.Interaction[QingqueClient], choice: PagingChoice):
        await inter.response.edit_message(
            embed=choice.embed,
            attachments=[choice.file] if choice.file is not None else [],
            view=self,
        )

    async def on_timeout(self) -> None:
        self._selection.disabled = True
        if hasattr(self, "_message"):
            await self._message.edit(view=None)

    async def start(self, inter: discord.InteractionMessage):
        self._message = inter
        first_val: dict[str, Any] = {
            "embed": self._choices[0].embed,
            "view": self,
        }
        if self._choices[0].file is not None:
            first_val["attachments"] = [self._choices[0].file]
        await inter.edit(**first_val)
