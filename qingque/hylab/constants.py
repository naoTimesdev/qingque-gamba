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

import yarl
from msgspec import Struct

from qingque.models.region import HYVRegion, HYVServer

__all__ = (
    "CHRONICLES_ROUTE",
    "CLAIM_ROUTE",
    "DAILY_ROUTE",
    "STARRAIL_SERVER",
    "STARRAIL_GAME_BIZ",
    "USER_AGENT",
    "DS_SALT",
    "Route",
)


class Route(Struct):
    """
    Represents a route for the HoyoLab API.
    """

    overseas: str | None = None
    """:class:`str | None`: The route for overseas servers."""
    china: str | None = None
    """:class:`str | None`: The route for Chinese servers."""

    def get_route(self, region: HYVRegion | HYVServer) -> yarl.URL:
        """:class:`str | None`: Get the route for the given region or server."""

        if isinstance(region, HYVServer):
            region = HYVRegion.from_server(region)
        if region == HYVRegion.China and self.china is not None:
            return yarl.URL(self.china)
        elif region == HYVRegion.Overseas and self.overseas is not None:
            return yarl.URL(self.overseas)
        raise ValueError(f"Invalid region {region!r}")


CHRONICLES_ROUTE = Route(
    overseas="https://bbs-api-os.hoyolab.com/game_record/hkrpg/api",
    china="https://api-takumi-record.mihoyo.com/game_record/app/hkrpg/api",
)
CLAIM_ROUTE = Route(
    overseas="https://sg-hkrpg-api.hoyoverse.com/common/apicdkey/api/webExchangeCdkey",
)
DAILY_ROUTE = Route(
    overseas="https://sg-public-api.hoyolab.com/event/luna/os?act_id=e202303301540311",
    china="https://api-takumi.mihoyo.com/event/luna/?act_id=e202304121516551",
)
STARRAIL_SERVER = {
    HYVServer.ChinaA: "prod_gf_cn",
    HYVServer.ChinaB: "prod_gf_cn",
    HYVServer.ChinaC: "prod_qd_cn",
    HYVServer.NorthAmerica: "prod_official_usa",
    HYVServer.Europe: "prod_official_eur",
    HYVServer.Asia: "prod_official_asia",
    HYVServer.Taiwan: "prod_official_cht",
}
STARRAIL_GAME_BIZ = {
    HYVRegion.China: "hkrpg_cn",
    HYVRegion.Overseas: "hkrpg_global",
}
DS_SALT = {
    HYVRegion.Overseas: "6s25p5ox5y14umn1p61aqyyvbvvl3lrt",
    HYVRegion.China: "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs",
    "cn_signin": "9nQiU3AV0rJSIBWgdynfoGMGKaklfbM7",
}
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0"
