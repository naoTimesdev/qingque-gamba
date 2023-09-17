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

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, TypeAlias, overload

from .base import RGB, RGBA, StarRailDrawing

if TYPE_CHECKING:
    from qingque.hylab.models.characters import ChronicleCharacter
    from qingque.hylab.models.forgotten_hall import ChronicleFHCharacter
    from qingque.hylab.models.simuniverse import ChronicleRogueCharacter
    from qingque.mihomo.models.characters import Character

    _HYLabCharacter: TypeAlias = ChronicleRogueCharacter | ChronicleFHCharacter | ChronicleCharacter


__all__ = (
    "SRDrawCharacter",
    "StarRailDrawCharacterMixin",
    "StarRailDrawGradientMixin",
)


class StarRailDrawGradientMixin:
    FIVE_GRADIENT: ClassVar[tuple[RGB, RGB]] = ((117, 70, 66), (201, 164, 104))
    FOUR_GRADIENT: ClassVar[tuple[RGB, RGB]] = ((55, 53, 87), (134, 89, 204))

    RARITY_COLOR: ClassVar[dict[int, RGB]] = {
        1: (83, 85, 95),
        2: (52, 75, 123),
        3: (152, 108, 82),
    }
    RARITY_GRADIANT: ClassVar[dict[int, tuple[RGB, RGB]]] = {
        1: ((49, 51, 64), (130, 131, 138)),
        2: ((45, 47, 81), (68, 116, 187)),
        3: FIVE_GRADIENT,
    }


@dataclass
class SRDrawCharacter:
    id: str
    level: int
    eidolons: int

    @overload
    @classmethod
    def from_mihomo(cls: type[SRDrawCharacter], character: Character) -> SRDrawCharacter:
        ...

    @overload
    @classmethod
    def from_mihomo(cls: type[SRDrawCharacter], character: list[Character]) -> list[SRDrawCharacter]:
        ...

    @classmethod
    def from_mihomo(
        cls: type[SRDrawCharacter], character: Character | list[Character]
    ) -> SRDrawCharacter | list[SRDrawCharacter]:
        characters = character if isinstance(character, list) else [character]
        mapped = list(
            map(
                lambda cc: cls(
                    id=str(cc.id),
                    level=cc.level,
                    eidolons=cc.eidolon,
                ),
                characters,
            )
        )
        return mapped if isinstance(character, list) else mapped[0]

    @overload
    @classmethod
    def from_hylab(cls: type[SRDrawCharacter], character: _HYLabCharacter) -> SRDrawCharacter:
        ...

    @overload
    @classmethod
    def from_hylab(cls: type[SRDrawCharacter], character: list[_HYLabCharacter]) -> list[SRDrawCharacter]:
        ...

    @classmethod
    def from_hylab(
        cls: type[SRDrawCharacter], character: _HYLabCharacter | list[_HYLabCharacter]
    ) -> SRDrawCharacter | list[SRDrawCharacter]:
        characters = character if isinstance(character, list) else [character]
        mapped = list(
            map(
                lambda cc: cls(
                    id=str(cc.id),
                    level=cc.level,
                    eidolons=cc.eidolon,
                ),
                characters,
            )
        )
        return mapped if isinstance(character, list) else mapped[0]


class StarRailDrawCharacterMixin:
    async def _create_character_card(
        self,
        characters: list[SRDrawCharacter],
        *,
        drawing: StarRailDrawing,
        margin_top: int,
        margin_lr: int,
        inbetween_margin: int,
        icon_size: int,
        box_color: RGB | RGBA | None = None,
        box_text_color: RGB | None = None,
    ) -> None:
        """Create the character card for the star rail.

        Parameters
        ----------
        characters: :class:`list[SRDrawCharacter]`
            The list of characters to draw.
        margin_top: :class:`int`
            The margin top of the character card.
        margin_lr: :class:`int`
            The margin left and right of the character card.
        inbetween_margin: :class:`int`
            The margin between each character.
        icon_size: :class:`int`
            The size of the character icon.
        drawing: :class:`StarRailDrawing`
            The drawing to use.
        """
        for idx, lineup in enumerate(characters):
            char_info = drawing._index_data.characters[lineup.id]

            chara_icon = await drawing._async_open(drawing._assets_folder / char_info.icon_url)
            chara_icon = await drawing._resize_image(chara_icon, (icon_size, icon_size))

            # Create the gradient background
            gradient = (
                StarRailDrawGradientMixin.FIVE_GRADIENT
                if char_info.rarity == 5
                else StarRailDrawGradientMixin.FOUR_GRADIENT
            )
            await drawing._create_box_2_gradient(
                (
                    margin_lr + (inbetween_margin * idx),
                    margin_top,
                    margin_lr + (inbetween_margin * idx) + chara_icon.width,
                    margin_top + chara_icon.height,
                ),
                gradient,
            )
            # Add the character icon
            await drawing._paste_image(
                chara_icon,
                (margin_lr + (inbetween_margin * idx), margin_top),
                chara_icon,
            )
            await drawing._async_close(chara_icon)

            # Backdrop for the level
            await drawing._create_box(
                (
                    (margin_lr + (inbetween_margin * idx), margin_top + chara_icon.height),
                    (
                        margin_lr + (inbetween_margin * idx) + chara_icon.height,
                        margin_top + chara_icon.height + 30,
                    ),
                ),
                color=box_color or drawing._foreground,
            )
            # Write the level
            await drawing._write_text(
                drawing._i18n.t("chronicles.level_short", [f"{lineup.level:02d}"]),
                (
                    margin_lr + (inbetween_margin * idx) + (chara_icon.width // 2),
                    margin_top + chara_icon.height + 22,
                ),
                font_size=20,
                anchor="ms",
                color=box_text_color or drawing._background,
            )

            # Create backdrop for eidolons (top right)
            await drawing._create_box(
                (
                    (margin_lr + (inbetween_margin * idx) + chara_icon.width - 31, margin_top),
                    (margin_lr + (inbetween_margin * idx) + chara_icon.width - 1, margin_top + 30),
                ),
                color=box_color or (*drawing._foreground, round(0.8 * 255)),
            )
            # Write the eidolon
            await drawing._write_text(
                f"E{lineup.eidolons}",
                (margin_lr + (inbetween_margin * idx) + chara_icon.width - 16, margin_top + 22),
                font_size=20,
                anchor="ms",
                color=box_text_color or drawing._background,
            )
            # Create the element icon
            await drawing._create_circle(
                [
                    margin_lr + (inbetween_margin * idx) + 2,
                    margin_top + 2,
                    margin_lr + (inbetween_margin * idx) + 33,
                    margin_top + 33,
                ],
                color=(*drawing._background, 128),
                width=0,
            )
            element_icon = await drawing._async_open(drawing._assets_folder / char_info.element.icon_url)
            # Element icon are 28x28 for 150x150 icon
            # Try to scale accordingly
            element_icon_size = round(28 * (icon_size / 150))
            element_icon = await drawing._resize_image(element_icon, (element_icon_size, element_icon_size))
            # Paste Top-left corner
            await drawing._paste_image(
                element_icon,
                (margin_lr + (inbetween_margin * idx) + 3, margin_top + 3),
                element_icon,
            )
            await drawing._async_close(element_icon)
