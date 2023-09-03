# Qingque Gamba

![Qingque my beloved](https://p.ihateani.me/toufriwg.png "Qingque my Beloved")
![Hoyolab Profile](https://p.ihateani.me/whfxlqze.png "Hoyolab Profile")

A simple Discord Interaction bot to see your Honkai: Star Rail profile

## Add

[Invite](https://discord.com/api/oauth2/authorize?client_id=1146085026086264953&permissions=412317240384&scope=bot%20applications.commands)

## Running it Yourself

**Requirements**:
- Python 3.10+
- Poetry
- Redis Database
- Working server

1. Run `poetry install` to install all deps
2. Create `config.toml` from `config.toml.example` and fill everything.
3. Start bot by running `poetry run srsbot`

You can also generate your card without the bot by just running: `poetry run srscard [UID]` (See `poetry run srscard --help` for more info)

## To be Implemented
- [x] Deploy it for public use
- [ ] Profile card
- [ ] Battle chronicles stuff
  - [x] Overview/Real-time notes
  - [ ] Simulated Universe/Rogue
  - [ ] Forgotten Hall/Memory of Chaos/Abyss
- [ ] Relic scoring system (borrowed either from MobileMeta or Mar-7th)

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