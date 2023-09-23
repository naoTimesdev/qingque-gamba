# Qingque Gamba

![Qingque my beloved](https://p.ihateani.me/toufriwg.png "Qingque my Beloved")
![Hoyolab Profile](https://p.ihateani.me/hfcapbkw.png "Hoyolab Profile")

<div align="center">
<a href="https://github.com/psf/black" target="_blank"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black"></a>&nbsp;<a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>&nbsp;<a href="https://github.com/naoTimesdev/qingque-gamba/blob/master/LICENSE"><img src="https://img.shields.io/github/license/naoTimesdev/qingque-gamba"></a>&nbsp;<a href="https://crowdin.com/project/qingque-gamba" target="_blank"><img src="https://badges.crowdin.net/qingque-gamba/localized.svg" alt="Crowdin Localization" /></a>
<br/><br/>
A simple Discord Interaction bot to see your Honkai: Star Rail profile
</div>
<div align="center">
<a href="https://discord.com/api/oauth2/authorize?client_id=1146085026086264953&permissions=412317240384&scope=bot%20applications.commands">Invite</a> | <a href="https://crowdin.com/project/qingque-gamba">Translate</a>
</div>

## Features
- Account binding
- Automatic localization depending on your Discord language! ![Localization Progress](https://badges.crowdin.net/qingque-gamba/localized.svg)
- Character profile card
- Battle Chronicles (via HoyoLab)
- Simulated Universe (via HoyoLab)
- Memory of Chaos (via HoyoLab)
- Daily reward claim (HoyoLab)
- Relic scoring (See: [Relic Scoring](https://github.com/naoTimesdev/qingque-gamba/wiki/Relic-Scoring))
- **[TODO]** Redemption code claim

## Running it Yourself

**Requirements**:
- Python 3.10+
- Poetry
- Redis Database
- Working server

**Running**:
1. Run `poetry install` to install all deps
2. Create `config.toml` from `config.toml.example` and fill everything.
3. Start bot by running `poetry run srsbot`

You can also generate your card without the bot by just running: `poetry run srscard [UID]` (See `poetry run srscard --help` for more info)

### Rate Limited?

See here: [`naoTimesdev/qingque-data` Rate Limited](https://github.com/naoTimesdev/qingque-data#rate-limited)

## Credits
- Original Mihomo API implementation: https://github.com/kT-Yeh/mihomo/ (Yoinked most of the code and rewrite it using `msgspec`)
- StarDB.gg: https://stardb.gg/ (I basically ripped their design styles and decide to reimplement it and tweaks)
  - Some difference are:
    - Relic set bonus information
    - Show avatar
    - More iconography
    - Better skills view (Show major trace, alignment issue, etc.)
    - Fixed a ton of centering issue
    - Better information for Element/Path
    - Add rarity star
    - Margin adjustment
    - Use font that are used in-game
- Mar-7th StarRailRes: https://github.com/Mar-7th/StarRailRes (I'm using assets from here and saved it locally.)
- thesadru genshin.py: https://github.com/thesadru/genshin.py (Used some of their code for my own HoyoLab client.)
- miHoYo/Honkai: Star Rail — As all the fonts/assets are taken from the game, all rights reserved.

# Copyright

The code in this repository is owned by [naoTimesdev](https://github.com/naoTimesdev), the code is released under the [MIT License](LICENSE). Original assets and fonts used in this project are sourced from the game Honkai: Star Rail, developed by miHoYo. All rights to these assets and fonts belong to miHoYo and/or COGNOSPHERE PTE LTD, and they are used here for our profile generator purposes only. Additionally, this project has taken inspiration from other projects, which are credited in the [Credits](#credits) section. The license terms for any incorporated elements depend on the individual projects from which they were sourced.
