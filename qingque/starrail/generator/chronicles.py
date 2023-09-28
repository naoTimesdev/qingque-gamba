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

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from qingque.hylab.models.notes import ChronicleNotes
from qingque.hylab.models.overview import ChronicleOverview, ChronicleUserInfo, ChronicleUserOverview
from qingque.mihomo.models.constants import MihomoLanguage
from qingque.tooling import get_logger

from .base import StarRailDrawing, StarRailDrawingLogger
from .mixins import StarRailDrawDecoMixin

if TYPE_CHECKING:
    from qingque.hylab.models.base import HYLanguage
    from qingque.i18n import QingqueLanguage
    from qingque.starrail.loader import SRSDataLoader

__all__ = ("StarRailChronicleNotesCard",)


class StarRailChronicleNotesCard(StarRailDrawDecoMixin, StarRailDrawing):
    MARGIN_LR = 75
    MARGIN_IMGT = 10

    def __init__(
        self,
        overview: ChronicleUserOverview,
        chronicle: ChronicleNotes,
        *,
        language: MihomoLanguage | HYLanguage | QingqueLanguage = MihomoLanguage.EN,
        loader: SRSDataLoader | None = None,
    ) -> None:
        super().__init__(language=language, loader=loader)
        self._chronicle: ChronicleNotes = chronicle

        overall = overview.overview
        if overall is None:
            raise RuntimeError("Overview is not provided.")
        user_info = overview.user_info
        if user_info is None:
            raise RuntimeError("User info is not provided.")
        self._overview: ChronicleOverview = overall
        self._user_info: ChronicleUserInfo = user_info
        self.logger = get_logger(
            "qingque.starrail.generator.chronicles",
            adapter=StarRailDrawingLogger.create(self._user_info.name),
        )

        self._make_canvas(width=1600, height=900, color=(18, 18, 18))

        # Actual panel would be from 75, 75 to 1475, 797.

        self._background = (18, 18, 18)
        self._foreground = (219, 194, 145)

    async def _create_overview_info(self) -> None:
        # Create the days active
        ## Icon first
        days_icon_top = 200
        days_top = days_icon_top + 25
        active_icon = await self._async_open(
            self._assets_folder / "icon" / "sign" / "CommonTabIcon.png",
        )
        active_icon = await self._tint_image(active_icon, self._foreground)
        await self._paste_image(
            active_icon,
            (self.MARGIN_LR - 5, days_icon_top),
            active_icon,
        )
        await self._write_text(
            content=self._i18n.t("chronicles.days_active") or "Days Active",
            box=(self.MARGIN_LR + self.MARGIN_IMGT + active_icon.width, days_top + 20),
            font_size=30,
            anchor="ls",
            align="left",
            alpha=round(0.75 * 255),
        )
        await self._write_text(
            content=f"{self._overview.stats.active:,}",
            box=(self.MARGIN_LR + self.MARGIN_IMGT + active_icon.width, days_top + 45),
            font_size=40,
            anchor="lt",
            align="left",
        )

        # Avatar/Characters
        avatar_image_top = days_top + 125
        avatar_top = avatar_image_top + 25
        avatar_icon = await self._async_open(
            self._assets_folder / "icon" / "sign" / "AvatarIcon.png",
        )
        avatar_icon = await self._tint_image(avatar_icon, self._foreground)
        await self._paste_image(
            avatar_icon,
            (self.MARGIN_LR - 5, avatar_image_top),
            avatar_icon,
        )
        await self._write_text(
            content=self._i18n.t("chronicles.characters") or "Characters",
            box=(self.MARGIN_LR + self.MARGIN_IMGT + avatar_icon.width, avatar_top + 20),
            font_size=30,
            anchor="ls",
            align="left",
            alpha=round(0.75 * 255),
        )
        await self._write_text(
            content=f"{self._overview.stats.characters:,}",
            box=(self.MARGIN_LR + self.MARGIN_IMGT + avatar_icon.width, avatar_top + 45),
            font_size=40,
            anchor="lt",
            align="left",
        )

        # Achivements
        achivement_image_top = avatar_top + 125
        achivement_top = achivement_image_top + 25
        achivement_icon = await self._async_open(
            self._assets_folder / "icon" / "sign" / "AchievementIcon.png",
        )
        achivement_icon = await self._tint_image(achivement_icon, self._foreground)
        await self._paste_image(
            achivement_icon,
            (self.MARGIN_LR - 5, achivement_image_top),
            achivement_icon,
        )
        await self._write_text(
            content=self._i18n.t("chronicles.achievements") or "Achievements",
            box=(self.MARGIN_LR + self.MARGIN_IMGT + achivement_icon.width, achivement_top + 20),
            font_size=30,
            anchor="ls",
            align="left",
            alpha=round(0.75 * 255),
        )
        await self._write_text(
            content=f"{self._overview.stats.achievements:,}",
            box=(self.MARGIN_LR + self.MARGIN_IMGT + achivement_icon.width, achivement_top + 45),
            font_size=40,
            anchor="lt",
            align="left",
        )

        # Abyss/Forgotten Hall/Memory of Chaos
        if self._overview.stats.moc_floor:
            abyss_image_top = achivement_top + 125
            abyss_top = abyss_image_top + 30
            abyss_icon = await self._async_open(
                self._assets_folder / "icon" / "sign" / "AbyssIcon02.png",
            )
            abyss_icon = await self._tint_image(abyss_icon, self._foreground)
            await self._paste_image(
                abyss_icon,
                (self.MARGIN_LR - 5, abyss_image_top),
                abyss_icon,
            )
            await self._write_text(
                content=self._i18n.t("chronicles.moc") or "Memory of Chaos",
                box=(self.MARGIN_LR + self.MARGIN_IMGT + abyss_icon.width, abyss_top + 20),
                font_size=30,
                anchor="ls",
                align="left",
                alpha=round(0.75 * 255),
            )
            await self._write_text(
                content=self._overview.stats.moc_floor,
                box=(self.MARGIN_LR + self.MARGIN_IMGT + abyss_icon.width, abyss_top + 45),
                font_size=24,
                anchor="lt",
                align="left",
            )

            # Close the image.
            await self._async_close(abyss_icon)

        # Close the images.
        await self._async_close(active_icon)
        await self._async_close(avatar_icon)
        await self._async_close(achivement_icon)

    async def _create_chronicle_notes(self) -> None:
        # All notes are right aligned.
        # TB Power
        tb_power_top = 200
        tb_power_icon = await self._async_open(
            self._assets_folder / "icon" / "item" / "11.png",
        )

        await self._paste_image(
            tb_power_icon,
            (self._canvas.width - tb_power_icon.width - self.MARGIN_LR + 5, tb_power_top),
            tb_power_icon,
        )
        await self._write_text(
            content=self._i18n.t("chronicles.tb_power") or "Trailblaze Power",
            box=(self._canvas.width - tb_power_icon.width - self.MARGIN_LR - self.MARGIN_IMGT, tb_power_top + 25 + 20),
            font_size=30,
            anchor="rs",
            align="right",
            alpha=round(0.75 * 255),
        )
        await self._write_text(
            content=f"{self._chronicle.stamina:,}/{self._chronicle.max_stamina:,}",
            box=(self._canvas.width - tb_power_icon.width - self.MARGIN_LR - self.MARGIN_IMGT, tb_power_top + 70),
            font_size=40,
            anchor="rt",
            align="right",
        )

        # Reserve TB Power
        reserve_tb_power_top = tb_power_top + 135
        reserve_tb_power_icon = await self._async_open(
            self._assets_folder / "icon" / "item" / "12.png",
        )
        reserve_tb_power_icon = await self._resize_image(reserve_tb_power_icon, (112, 112))

        await self._paste_image(
            reserve_tb_power_icon,
            (self._canvas.width - reserve_tb_power_icon.width - self.MARGIN_LR - 5, reserve_tb_power_top + 10),
            reserve_tb_power_icon,
        )
        await self._write_text(
            content=self._i18n.t("chronicles.reserve_tb_power") or "Reserved Trailblaze Power",
            box=(
                self._canvas.width - tb_power_icon.width - self.MARGIN_LR - self.MARGIN_IMGT,
                reserve_tb_power_top + 25 + 20,
            ),
            font_size=30,
            anchor="rs",
            align="right",
            alpha=round(0.75 * 255),
        )
        await self._write_text(
            content=f"{self._chronicle.reserve_stamina:,}",
            box=(
                self._canvas.width - tb_power_icon.width - self.MARGIN_LR - self.MARGIN_IMGT,
                reserve_tb_power_top + 70,
            ),
            font_size=40,
            anchor="rt",
            align="right",
        )

        # Daily Training
        train_icon_top = reserve_tb_power_top + 145
        train_top = train_icon_top + 25
        train_icon = await self._async_open(
            self._assets_folder / "icon" / "sign" / "DailyQuestIcon.png",
        )
        train_icon = await self._tint_image(train_icon, self._foreground)

        await self._paste_image(
            train_icon,
            (self._canvas.width - train_icon.width - self.MARGIN_LR + 5, train_icon_top),
            train_icon,
        )
        await self._write_text(
            content=self._i18n.t("chronicles.daily_quest") or "Daily Training",
            box=(self._canvas.width - train_icon.width - self.MARGIN_LR - self.MARGIN_IMGT, train_top + 20),
            font_size=30,
            anchor="rs",
            align="right",
            alpha=round(0.75 * 255),
        )
        await self._write_text(
            content=f"{self._chronicle.training_score:,}/{self._chronicle.training_max_score:,}",
            box=(self._canvas.width - train_icon.width - self.MARGIN_LR - self.MARGIN_IMGT, train_top + 45),
            font_size=40,
            anchor="rt",
            align="right",
        )

        # Echo of War
        echo_icon_top = train_top + 125
        echo_top = echo_icon_top + 25
        echo_icon = await self._async_open(
            self._assets_folder / "icon" / "sign" / "CocoonIcon.png",
        )
        echo_icon = await self._tint_image(echo_icon, self._foreground)

        await self._paste_image(
            echo_icon,
            (self._canvas.width - echo_icon.width - self.MARGIN_LR + 5, echo_icon_top),
            echo_icon,
        )
        await self._write_text(
            content=self._i18n.t("chronicles.echo_of_war") or "Echo of War",
            box=(self._canvas.width - echo_icon.width - self.MARGIN_LR - self.MARGIN_IMGT, echo_top + 20),
            font_size=30,
            anchor="rs",
            align="right",
            alpha=round(0.75 * 255),
        )
        await self._write_text(
            content=f"{self._chronicle.eow_available:,}/{self._chronicle.eow_limit:,}",
            box=(self._canvas.width - echo_icon.width - self.MARGIN_LR - self.MARGIN_IMGT, echo_top + 45),
            font_size=40,
            anchor="rt",
            align="right",
        )

        # Close the images.
        await self._async_close(tb_power_icon)
        await self._async_close(reserve_tb_power_icon)
        await self._async_close(train_icon)
        await self._async_close(echo_icon)

    async def create(self, *, hide_credits: bool = False, hide_timestamp: bool = False) -> bytes:
        self._assets_folder = await self._assets_folder.absolute()
        if not await self._assets_folder.exists():
            raise FileNotFoundError("The assets folder does not exist.")
        await self._index_data.async_loads()

        # Use custom backdrop
        backdrop_img = await self._async_open(self._assets_folder / "image" / "backdrops" / "BackdropLoadingV2.png")
        # Crop bottom part (16px)
        # Also keep the width centered to 16:9
        bg_h_crop = 27
        bg_w_left_c = 0 + (backdrop_img.width - ((backdrop_img.height - bg_h_crop) * (16 / 9))) // 2
        bg_w_right_c = backdrop_img.width - bg_w_left_c
        backdrop_img = await self._crop_image(
            backdrop_img, (bg_w_left_c, 0, bg_w_right_c, backdrop_img.height - bg_h_crop)
        )
        # Resize to 1600x900
        backdrop_img = await self._resize_image(backdrop_img, (1600, 900))
        # Paste it
        await self._paste_image(backdrop_img, (0, 0), backdrop_img)
        await self._async_close(backdrop_img)

        # Create the decoration.
        self.logger.info("Creating decoration...")
        await self._create_decoration(hide_credits, drawing=self)

        # Write the username.
        self.logger.info("Writing username...")
        await self._write_text(
            content=self._user_info.name,
            box=(self.MARGIN_LR, 75),
            font_size=86,
            anchor="lt",
        )

        # Do the overview info.
        self.logger.info("Creating overview info...")
        await self._create_overview_info()
        # Do the chronicle notes.
        self.logger.info("Creating chronicle notes...")
        await self._create_chronicle_notes()

        # Create footer
        self.logger.info("Creating footer...")
        await self._write_text(
            "Supported by Interastral Peace Corporation",
            (20, self._canvas.height - 20),
            font_size=20,
            alpha=128,
            font_path=self._universe_font_path,
            anchor="ls",
        )

        # Create a timestamp (top right)
        if not hide_timestamp:
            dt = datetime.utcfromtimestamp(self._chronicle.requested_at)
            # Shift to UTC+8
            dt = dt.replace(tzinfo=timezone.utc).astimezone(tz=timezone(timedelta(hours=8)))
            # Format to Day, Month YYYY HH:MM
            await self._write_text(
                self.format_timestamp(dt),
                (20, 20),
                font_size=20,
                anchor="lt",
                align="left",
                alpha=round(0.2 * 255),
            )

        # Create the credits
        if not hide_credits:
            await self._write_text(
                self._i18n.t("chronicles.credits") or "Data from HoyoLab | Created by @noaione",
                (self._canvas.width // 2, self._canvas.height - 20),
                font_size=16,
                alpha=128,
                anchor="ms",
            )

        # Save the image.
        self.logger.info("Saving the image...")
        bytes_io = await self._async_save_bytes(self._canvas)

        self.logger.info("Cleaning up...")
        await self._async_close(self._canvas)

        # Return the bytes.
        bytes_io.seek(0)
        all_bytes = await self._loop.run_in_executor(None, bytes_io.read)
        bytes_io.close()
        return all_bytes
