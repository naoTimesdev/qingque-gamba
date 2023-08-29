# Qingque Gamba

![Qingque my beloved](https://p.ihateani.me/wfrjtmor.png "Qingque my Beloved")

A simple Discord Interaction bot to see your Honkai: Star Rail profile

## Add

[Invite](https://discord.com/api/oauth2/authorize?client_id=1146085026086264953&permissions=277025770560&scope=bot)

## Running it Yourself

**Requirements**:
- Python 3.10+
- Redis Database
- Working server

## To be Implemented
- [ ] Deploy it for public use
- [ ] Profile card
- [ ] Battle chronicles stuff
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