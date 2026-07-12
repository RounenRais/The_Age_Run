# The_Age_Run
# The_Age_Run
<div align="center">

# 🧬 EVOLUTION SURVIVORS

### *From cell to godhood — die, evolve, repeat.*

A retro-arcade **roguelite survivor** built in Python + Pygame.
*Vampire Survivors* combat, *Brotato* build slots, wrapped in a *Spore*-style journey
through five eras of evolution — each with its own enemies, weapons, boss and UI theme.

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor
=white)
![Pygame](https://img.shields.io/badge/pygame-2.6-11B048?style=for-the-badge)
![Platform](https://img.shields.io/badge/platform-win%20%7C%20mac%20%7C%20linux-8A2BE2?style=for-the-b
adge)

<img src="docs/screenshots/main_menu.png" width="820" alt="Main menu">

</div>

---

## Table of Contents

- [What is it?](#what-is-it)
- [Gallery](#gallery)
- [Install & Run](#install--run)
- [Controls](#controls)
- [How a Run Works](#how-a-run-works)
- [The Five Eras](#the-five-eras)
- [Currencies](#currencies)
- [Weapons & Passives](#weapons--passives)
- [The Laboratory (Meta Progression)](#the-laboratory-meta-progression)
- [Project Structure](#project-structure)
- [Tweaking the Game](#tweaking-the-game)

---

## What is it?

You start as a single-celled blob with one weak spike. Weapons **fire on their own** — your
only job is to *position*. Survive waves, hoover up XP, level up, kill the era boss, evolve,
and repeat until something eats you.

Dying is the point. A run resets everything **except Evolution Points**, which you spend in
the Laboratory on permanent mutations. Beating all five eras on a fresh save is essentially
impossible; you get there by dying a lot and coming back stronger.

| | |
|---|---|
| 🧫 **5 eras** | Cell → Creature → Tribe → Civilization → Space |
| ⚔️ **18 weapons** | 6 auto-fire behaviours: nearest, spread, orbit, aura, nova, chain |
| 💎 **16 passives** | HP, armor, crit, cooldown, regen, XP, pickup radius… |
| 👾 **20 enemy types** | plus elites, plus 5 unique bosses |
| 🧪 **10 meta upgrades** | permanent mutations bought with Evolution Points |
| 🕹️ **Era-reactive UI** | HUD palette, borders and cards re-theme every era |
| 🔊 **Zero-asset audio** | every sound effect is synthesized at runtime |

---

## Gallery

<table>
  <tr>
    <td width="50%"><img src="docs/screenshots/run_cell.png" alt="Cell era gameplay"></td>
    <td width="50%"><img src="docs/screenshots/level_up.png" alt="Level up screen"></td>
  </tr>
  <tr>
    <td><b>Cell Era</b> — auto-firing spikes, XP orbs, and a chunky arcade HUD that glows like a membr
ane.</td>
    <td><b>Level Up</b> — pick 1 of 3 cards: upgrade a weapon, take a new one, or grab a passive.</td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/boss_cell.png" alt="Mother Amoeba boss"></td>
    <td><img src="docs/screenshots/boss_final.png" alt="Godlike Entity final boss"></td>
  </tr>
  <tr>
    <td><b>Mother Amoeba</b> — the Cell Era boss splits into smaller copies as you chew through it.</t
d>
    <td><b>Godlike Entity</b> — the multi-phase final boss, with screen-covering bullet-hell patterns.
</td>
  </tr>
  </tr>
  <tr>
    <td><b>Era Transition</b> — drag a new era's card straight onto a build slot to add or replace it,
 then spend leftover Energy in the mini-shop.</td>
    <td><b>The Laboratory</b> — spend Evolution Points on permanent mutations and weapon unlocks betwe
en runs.</td>
  </tr>
  <tr>
    <td colspan="2"><img src="docs/screenshots/game_over.png" alt="Game over screen"></td>
  </tr>
  <tr>
    <td colspan="2" align="center"><b>Game Over</b> — Energy, levels and weapons are gone. The Evoluti
on Points are yours to keep. Run it back.</td>
  </tr>
</table>

---

## Install & Run

```bash
# Python 3.10+ required
pip install pygame-ce      # or: pip install pygame
python main.py
```

No build step and nothing to download — sprites, fonts and icons ship in `assets/`, and all
sound is generated in code.

---

## Controls

| Key | Action |
|-----|--------|
| `WASD` / `Arrow keys` | Move (360°) — **weapons aim and fire themselves** |
| `1` `2` `3` | Pick a card on the level-up screen (or just click it) |
| `Mouse` | Menus, the Laboratory, drag-and-drop on the era transition screen |
| `ESC` | Pause / back |
| `Enter` | Confirm |
| `F11` | Fullscreen |
| `F3` | FPS counter |
| `F2` | Toggle the CRT / scanline overlay |

---

        ┌──────────── you die, keep your Evolution Points ────────────┐
        │                                                             ▼
   LABORATORY ──▶ ERA (5 waves) ──▶ BOSS ──▶ BUILD SELECT ──▶ next ERA…
                       │                                              │
                       └── level up every few kills (1 of 3 cards)    │
                          clear Era 5 = VICTORY ◀────────────────────-┘
```

1. **Waves.** Each era is 5 waves of ~60–75 seconds. Spawn rate climbs, enemy HP scales, and from
   wave 2 on a single **elite** shows up — kill it and it drops Evolution Points on the spot.
2. **Level-ups.** XP orbs level you constantly. Each level offers 3 cards: level a weapon (max 8),
   take a new weapon, take or level a passive (max 5), or heal.
3. **Boss.** Wave 6 is the era boss. It won't let you leave until it's dead.
4. **Era transition.** The screen morphs into the next era's palette and offers 3–4 era-specific
   builds. Drag one onto a slot to add or replace it, reorder your weapons, spend leftover Energy
   in the mini-shop (full heal / +10% damage / +8% speed), then confirm.
5. **Death.** Any era, any time. Stats are tallied, Evolution Points bank, and you're back in the
   Laboratory a little stronger than last time.

A full five-era clear runs roughly **40–60 minutes**.

---

## The Five Eras

| # | Era | Enemies | Boss | UI Theme |
|---|-----|---------|------|----------|
| 1 | **Cell** | Amoeba, Bacteria, Virus | 🦠 **Mother Amoeba** — splits into copies as it takes damag
e | Teal glow, organic pulse |
| 2 | **Creature** | Insect, Raptor, Beast | 🐾 **Alpha Predator** — fast, lunging claw attacks | Eart
hy orange, jagged edges |
| 3 | **Tribe** | Wolf, Hunter, Brute | 🔥 **Tribal Shaman** — summons and area magic | Fire-orange, t
orch flicker |
| 4 | **Civilization** | Soldier, Drone, Armored Unit | 🛡️ **War Machine** — armored, shelling artille
ry | Industrial red steel |
| 5 | **Space** | Alien, Robot, Energy Being | ⭐ **Godlike Entity** — three phases, bullet-hell | Neo
n purple/cyan hologram |

The theme swap isn't paint on a single screen: palette, panel borders, HUD banner and card
styling all key off the era index, so the whole interface visibly evolves alongside you.

---

## Currencies

<table>
<tr>
<td width="50%">

### ⚡ Energy — *in-run*

- Dropped by enemies, awarded on wave clears and boss kills
- Spent **during the run**, in the era-transition mini-shop
- **Wiped completely on death**

</td>
<td width="50%">

### 🧬 Evolution Points — *permanent*

- Bosses (20 → 120, scaling by era, plus a speed bonus)
- Wave clears, elite kills, and how far you got
- **Kept even when you die** — spent only in the Laboratory

</td>
</tr>
</table>

---

## Weapons & Passives

18 weapons across 6 auto-fire behaviours — you never control *what* fires, only *where you stand*:

| Behaviour | What it does | Examples |
|-----------|--------------|----------|
| `nearest` | Fires at the closest enemy | Pseudopod Spike, Throwing Spear, Rifle, Homing Missiles |
| `spread` | Cone of projectiles | Venom Spit, Stone Sling |
| `orbit` | Orbiting damage bodies | Cilia Whirl, Talon Sweep, Combat Drone |
| `aura` | Constant damage field around you | Toxin Cloud, Fire Totem, Singularity Core |
| `nova` | Radial burst outward | Quill Burst, Plasma Nova |
| `chain` | Arcs between enemies | Laser Module |

Weapons level to **8**, passives to **5**. You get **4 weapon slots** (6 with meta upgrades) and
**6 passive slots** — so past a point, adding something means *replacing* something, and that
tension is the whole game.

Three weapons — **Boomerang**, **Minigun** and **Singularity Core** — start locked and must be
bought in the Laboratory before they can ever appear in a run.

---

## The Laboratory (Meta Progression)

Ten permanent mutations, each with a rising cost curve (`base_cost × growth^level`):

| Mutation | Effect | Max Level | From |
|----------|--------|:---------:|------|
| **Vitality** | +15 starting Max HP | 6 | 25 EVO |
| **Primal Strength** | +6% weapon damage | 8 | 30 EVO |
| **Agility** | +4% move speed | 5 | 25 EVO |
| **Rapid Learning** | +8% XP gain | 5 | 30 EVO |
| **Cell Regeneration** | +0.4 HP/sec | 4 | 40 EVO |
| **Carapace** | +1 flat armor | 4 | 45 EVO |
| **Scavenger** | +15% Energy gain | 4 | 25 EVO |
| **Evolution Mastery** | +10% Evolution Points earned | 4 | 60 EVO |
| **Extra Limb** | +1 weapon slot | 2 | 150 EVO |
| **Second Genesis** | Revive once per run at 50% HP | 1 | 300 EVO |

Points, unlocks, upgrade levels and lifetime stats are written to `save.json`, auto-saved when
you return to the hub or close the game.

---

## Project Structure

```
main.py                  # game loop, state machine, CRT overlay, F-key handling
states/                  # one file per screen
  main_menu.py  hub.py  run_state.py  build_select.py
  pause.py  game_over.py  victory.py
entities/                # player, enemy, boss, projectile, pickup, particles
systems/
  asset_loader.py        # sprite/icon loading + procedural fallbacks
  audio.py               # runtime-synthesized SFX (no audio files)
ui/
  theme.py               # per-era palettes, panels, pixel fonts
  hud.py  widgets.py     # HUD, arcade cards and buttons
data/                    # all balance lives here, as JSON
  eras.json  weapons.json  accessories.json  enemies.json  upgrades.json
assets/                  # player/  enemies/  bosses/  icons/  fonts/
Everything is **delta-time driven** at a fixed 60 FPS target, so behaviour stays identical
regardless of the frame rate the machine actually hits.

---

## Tweaking the Game

Balance is data-driven — most changes need no code at all:

---

## Credits

- **Sprites** — [Dungeon Crawl Stone Soup](https://github.com/crawl/crawl) tile set (CC0 / public doma
in)
- **Font** — [Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P) by CodeMan38 (SIL OFL
1.1)
- **Audio** — synthesized at runtime in `systems/audio.py`

Full attribution in [CREDITS.md](CREDITS.md).

<div align="center">

**Now go get eaten by an amoeba.** 🧫

</div>
