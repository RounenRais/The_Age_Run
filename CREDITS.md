# Credits

## Fonts
- **Press Start 2P** by CodeMan38 — SIL Open Font License 1.1
  Source: https://fonts.google.com/specimen/Press+Start+2P
  File: `assets/fonts/PressStart2P.ttf`

## Sprites
- **Dungeon Crawl Stone Soup tile set (rltiles)** — CC0 / public domain
  Source: https://github.com/crawl/crawl (crawl-ref/source/rltiles/mon)
  Used for all player forms (`assets/player/`), enemies (`assets/enemies/`)
  and bosses (`assets/bosses/`), 25 tiles total. Thanks to the DCSS tile
  artists (Denzi, Ontoclasm, and other contributors) who released these
  tiles into the public domain.

Any sprite can be replaced by dropping a PNG at
`assets/<category>/<key>.png` (e.g. `assets/enemies/amoeba.png`) — the
asset loader (`systems/asset_loader.py`) picks files up automatically and
falls back to procedural art for missing keys (weapon/UI icons still use
the procedural generator).

## Audio
All sound effects are synthesized at runtime (`systems/audio.py`).
