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

import discord
from discord.interactions import Interaction

from qingque.bot import QingqueClient

__all__ = ("EmbedPaginatedView",)


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
        self._index = 1
        self.update_buttons(1)

    async def on_timeout(self) -> None:
        self.previous.disabled = True
        self.next.disabled = True
        if hasattr(self, "_message"):
            embed = self._embeds[self._index - 1]
            await self._message.edit(view=None, embed=embed)

    async def interaction_check(self, interaction: Interaction[QingqueClient]) -> bool:
        return interaction.user.id == self._user_id

    def update_buttons(self, current_page: int):
        total_page = len(self._embeds)
        self._index = current_page
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

    async def _edit(self, interaction: discord.Interaction):
        send_thing = {
            "embed": self._embeds[self._index - 1],
            "view": self,
        }
        await interaction.response.edit_message(**send_thing)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, disabled=True)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.update_buttons(self._index - 1)
        await self._edit(interaction)

    @discord.ui.button(label="Page 1/1", style=discord.ButtonStyle.secondary, disabled=True)
    async def count(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, disabled=True)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.update_buttons(self._index + 1)
        await self._edit(interaction)

    async def start(self, interaction: discord.Interaction[QingqueClient]):
        self._interaction = interaction
        send_thing = {
            "embed": self._embeds[self._index],
            "view": self,
        }
        if self._files is not None:
            send_thing["attachments"] = self._files
        original = await interaction.original_response()
        self._message = original
        await original.edit(**send_thing)
