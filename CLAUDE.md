# PROMPT: "EVOLUTION SURVIVORS" — Pygame Roguelite Game Development

Give the following document as-is as a prompt to Claude Fable 5 (or whichever model will write the code). It covers all game systems, balancing, and technical requirements.

---

## 1. GAME CONCEPT (One Sentence)

Build a 2D top-down **roguelite survivor** game: gameplay is a mix of *Vampire Survivors* + *Brotato*, theme/progression is inspired by *Spore* — the player evolves through 5 eras starting from the Cell era all the way to the Space era, each era ends with a boss, dying sends the run back to the start, but a persistent (meta) progression system means every death makes the next attempt stronger.

## 2. TECHNICAL REQUIREMENTS

- **Language/Library:** Python 3 + Pygame (pygame-ce is acceptable)
- **Platform:** Desktop (Windows/Linux/Mac), single-player
- **Resolution:** 1280x720 window, should be scalable (fullscreen toggle F11)
- **FPS:** Fixed 60, use delta-time-based movement/physics (frame-rate independent)
- **Code architecture:** Use a state machine structure:
  - `MainMenuState`, `HubState` (meta-progression menu), `RunState` (the actual game), `BuildSelectState` (era-transition screen), `PauseState`, `GameOverState`, `VictoryState`
- **Suggested and required file structure:**
  ```
  /main.py
  /states/
  /entities/ (player.py, enemy.py, boss.py, projectile.py, pickup.py)
  /systems/ (weapons.py, spawner.py, meta_progression.py, save_system.py)
  /data/ (weapons.json, accessories.json, enemies.json, eras.json, upgrades.json)
  /assets/ (sprite images — see Section 2a for sourcing)
  /ui/
  ```
- **Saving:** Meta-progression data (permanent currency, unlocked weapons, permanent upgrades) should be saved to a JSON file (`save.json`), auto-saved on game close / on returning to the hub.

### 2a. ART / SPRITES — USE REAL SPRITES, NOT PLACEHOLDER SHAPES

- Instead of drawing plain geometric shapes (circles/squares) for the player, enemies, bosses, weapons, and pickups, **fetch actual 2D sprite art from the internet** and use it in the game.
- Prioritize free, license-safe sources meant for game development, for example:
  - **OpenGameArt.org** (CC0 / CC-BY assets)
  - **Kenney.nl** (CC0, huge library of clean 2D game asset packs — top-down creatures, sci-fi units, particles, UI)
  - **itch.io** (filter by "free" and check the license on each asset pack before use)
- When downloading/using assets, check and respect the license (CC0 is safest/no attribution needed; CC-BY needs credit — if so, add a short `CREDITS.md` listing the source and author for each pack used).
- Organize downloaded sprites under `/assets/` by category (`/assets/player/`, `/assets/enemies/`, `/assets/bosses/`, `/assets/weapons/`, `/assets/ui/`, `/assets/vfx/`) and load them via a small asset-loading helper (`systems/asset_loader.py`) so paths aren't hardcoded everywhere.
- If a perfectly matching sprite can't be found for something very specific (e.g. a very particular boss silhouette), it's fine to reuse/recolor a close-enough sprite pack rather than blocking progress — visual consistency (a coherent pixel-art or vector style across the whole game) matters more than exact thematic accuracy.
- Simple shapes are only acceptable as a temporary placeholder during early prototyping (Section 8, steps 1-3) and should be replaced with real sprites once the corresponding system is confirmed working.

## 3. CORE GAMEPLAY LOOP (WITHIN A RUN)

- Player moves freely in 360° using WASD/arrow keys (top-down).
- Weapons **fire automatically** (Vampire Survivors logic) — the player doesn't aim, just positions themselves.
- Enemies spawn continuously, move toward the player, deal contact damage.
- Killed enemies drop **XP orbs** and **in-run currency (Energy)**.
- Collecting XP levels up the character → on level-up, the player picks 1 of 3 options (upgrade current weapon / gain a new passive / stat boost) — this is the classic Vampire Survivors-style level-up screen, DO NOT confuse this with the era transition, it's a separate, more frequent system.
- Each **era** consists of multiple **stages/waves** (suggestion: 4-6 waves per era + 1 boss wave). Waves get progressively harder over time (spawn rate increases, tougher enemy types are introduced).
- The last wave of an era spawns the **era boss**. You cannot advance to the next era until the boss is dead.
- Once the boss dies → **Era Transition / Build Select Screen** opens (see Section 5).
- If the player dies (HP reaches 0) → `GameOverState`: in-run gains (Energy, level, weapons) are reset, but the **meta currency (Evolution Points)** earned during that run is saved permanently → returns to `HubState`.

## 4. ERA SYSTEM (5 ERAS, SPORE THEME)

| # | Era Name | Theme/Visuals | Example Enemies | Boss Idea |
|---|----------|----------------|-------------------|-----------|
| 1 | Cell Era | Microscopic, organic, fluid environment | Amoeba, virus particle, bacteria swarm | Giant Mother Amoeba (splits/multiplies as a boss mechanic) |
| 2 | Creature Era | Primitive land/water creatures | Reptiles, insects, predator beasts | Alpha Predator (speed + claw attacks) |
| 3 | Tribe Era | Primitive humanoids, spears/fire | Tribal hunters, wild animals | Tribal Shaman (magic/area attacks) |
| 4 | Civilization Era | Army, technology, firearms | Soldiers, armored units, drones | Giant War Machine/Tank |
| 5 | Space Era | Space, stars, advanced technology | Alien soldiers, robots, energy beings | **Godlike Entity** (final boss — multi-phase, screen-covering attack patterns, the hardest fight in the game, multiple health bars/phases) |

**Duration target:** For an average, moderately skilled player, all 5 eras should take about ~40 minutes total. With cautious play or a tough run, it can stretch to up to 60 minutes. Deaths should be frequent in the early eras; finishing the game with **zero meta-upgrades** (pure vanilla run) should be **nearly impossible** — this is the core balancing rule that makes the meta-progression system meaningful.

## 5. ERA TRANSITION / BUILD SELECT SYSTEM

Screen that opens when a boss dies:

- The player is shown 3-4 options from a build pool **specific to the new era** (a new weapon, a new accessory, or a powerful passive ability).
- Each era has its own thematic build pool (e.g. Civilization Era might offer "Rifle", "Armor Plating"; Space Era might offer "Laser Module", "Shield Generator").
- **Builds acquired in previous eras stay in their slots** (they are not deleted).
- On this screen, the player can optionally **replace** an existing slot with the new selection — meaning each era transition doesn't force adding something new, an old build can be swapped out for the new era's power instead.
- There should be a slot limit (suggestion: 6 weapon slots + 6 accessory/passive slots, expandable via meta-upgrades — same logic as Brotato's slot system).
- This screen can also let the player spend accumulated in-run Energy for small immediate upgrades to current weapons/accessories (optional, gives a mini-shop feel between eras).

## 6. TWO-CURRENCY SYSTEM

### A) Energy (In-Run Currency — easy to earn, temporary)
- Earned from killing enemies, opening chests, finishing waves.
- Spent **only within the run**: on the level-up screen, on the era transition screen for minor upgrades, at in-run "altar/shop" stations for temporary buffs.
- **Fully resets** on death, does not carry over to the next run.

### B) Evolution Points / DNA Fragments (Meta Currency — hard to earn, permanent)
- Earning sources:
  - Killing an era boss (fixed amount + performance-based bonus)
  - Total run duration and era reached (the further you get, the more you earn)
  - Killing elite/special enemies (rare mini-bosses)
  - **Even if you die**, whatever Evolution Points you've accumulated so far is kept (no loss) — only the earn RATE is much slower than Energy.
- Spent only in `HubState` (main menu/lab screen), outside of runs.
- What it's spent on:
  - Unlocking new weapons/accessories (so they can appear in the build pool in future runs)
  - Permanent upgrades to already-unlocked weapons/accessories (base damage +%, base HP +, starting slot count +1, etc.)
  - Small permanent increases to the character's base stats (move speed, starting health, etc.)
- **Balancing rule:** The Evolution Points earn rate should follow a curve where the player "gradually gets strong enough to eventually clear era 5 through repeated deaths." Too slow feels grindy/boring, too fast makes the difficulty pointless. Roughly calibrate it so a player can comfortably reach era 3 within their first 10-15 runs, but clearing era 5 requires dozens of runs and careful meta-build choices.

## 7. WEAPON AND ACCESSORY SYSTEM (BROTATO-INSPIRED)

- Weapons are **passive/automatic**, the player only positions themselves.
- Each weapon has stats like: damage, fire rate, range, projectile count/type (single-target, area, chaining, etc.)
- Accessories don't attack directly, they modify stats (health regen, move speed, crit chance, XP gain, etc.)
- If the player gets multiple copies of the same weapon (or it appears again on level-up), that weapon should level up and get stronger (stacking/evolving logic, similar to weapon evolution in Vampire Survivors — e.g. 2 copies of a weapon + a specific accessory combo could turn into a special "evolved" version; this is a nice-to-have, not required for MVP).

## 8. MVP SCOPE (Priority Order for Initial Code)

Ask Fable to proceed in this order when writing code, keeping a working version at every step:

1. Basic state machine + empty window + FPS counter
2. Player movement (WASD) + rendered as a simple placeholder shape for now
3. One automatic weapon + enemy spawning system + collision/damage
4. XP/level-up system + basic level-up choice screen (pick 1 of 3)
5. Wave system for 1 era + 1 boss (Cell Era, fully playable)
6. Death → GameOver → Hub transition + basic meta currency saving (doesn't need to be spendable yet, just tracked)
7. In the Hub, spend meta currency on 2-3 simple permanent upgrades
8. Era transition/build select screen (test with Cell → Creature transition)
9. Fill in the remaining 4 eras with content for enemies/bosses/build pools
10. **Swap all placeholder shapes for real sprites fetched per Section 2a**
11. Polish: sound effects (placeholder beep sounds are fine too), screen shake, damage numbers, simple looping music, main menu, pause menu

## 9. UI/UX DESIGN — RETRO ARCADE STYLE, EVOLVING WITH EACH ERA

**Overall direction:** Chunky retro-arcade UI (think coin-op cabinet menus / classic arcade HUDs), NOT a clean minimalist modern UI. Thick pixel-art borders, blocky pixel fonts, high-contrast colors, subtle scanline/CRT flicker overlay on the whole screen for atmosphere. The UI itself should visually "evolve" as the player advances through eras, reinforcing the Spore-style progression at the interface level, not just in the game world.

### 9a. Era-Reactive UI Theme
- Define a UI theme/palette per era (colors, border style, font weight/decoration) and swap it whenever the player enters a new era. Suggested progression:
  - **Cell Era:** organic, rounded/blobby panel borders, green/teal glow, HUD elements pulse slightly like a heartbeat/cell membrane.
  - **Creature Era:** rougher, bone/claw-like jagged panel edges, earthy orange/brown tones.
  - **Tribe Era:** wood/stone-carved panel textures, fire-orange and stone-grey tones, torch-flicker glow on borders.
  - **Civilization Era:** clean metal/riveted panel borders, industrial grey/red, sharper geometric fonts.
  - **Space Era:** thin neon-line panel borders, deep purple/cyan glow, subtle holographic flicker effect.
- Implement this as a simple `ui_theme.py` / theme dictionary keyed by era index (colors, border asset, font) that all HUD/menu draw calls reference, so re-theming per era is a matter of swapping one config, not rewriting draw code.
- Keep a consistent arcade "chunkiness" (thick borders, bold pixel font, high contrast) across all eras — only the color palette and border decoration should shift, not the overall UI grammar (so it stays readable and consistent).

### 9b. In-Run HUD (`RunState`)
- **Top-left:** HP bar (chunky, segmented like classic arcade health bars) + numeric HP.
- **Top-center:** XP bar spanning most of the top edge, current level shown as a badge on top of it.
- **Top-right:** Energy (in-run currency) counter with a coin/orb icon, run timer (MM:SS).
- **Bottom or side (era-themed banner):** current era name + a small icon representing it (e.g. a cell icon, a rocket icon), plus a wave/boss progress indicator (e.g. "Wave 3/5" or a boss health bar when a boss is active, drawn as a large bar across the top of the screen during boss fights, arcade-boss-battle style).
- **Corner (bottom-left or bottom-right):** small icon row of currently equipped weapon/accessory slots (icons + level pips), so the player can glance at their current build without pausing.
- Damage taken triggers a brief red vignette flash + screen shake; XP pickups give a small particle trail toward the player.

### 9c. Level-Up Screen (mid-run, frequent)
- Game pauses, screen dims/darkens behind, 3 large arcade-style "cards" appear side by side in the center (icon, name, short stat description, rarity-colored border).
- Selected card on hover/highlight scales up slightly and glows using the current era's accent color.
- Quick to read and pick — this happens often, so keep it fast (no long animations blocking input).

### 9d. Era Transition / Build Select Screen
- More ceremonial than the level-up screen — this is a bigger moment. Full-screen takeover with a brief "era complete" banner/animation transitioning the background from the old era's theme to the new one (e.g. a screen-wipe or morph effect using the era color palettes).
- Below the banner: the 3-4 new era-specific build options as large cards (same card language as level-up, but bigger, with more flavor text — this is meant to feel like a bigger decision).
- Below that: a **build slot row** showing all currently-equipped weapons/accessories (from previous eras) as icons; the player can click an existing slot to mark it for replacement before confirming a new pick. Slots filled by the current era should get a subtle themed glow/badge showing which era they came from (helps the player see their build's "evolutionary history" at a glance).
- Optional mini-shop row at the bottom for spending leftover Energy on small immediate upgrades before continuing.

### 9e. Hub Screen (`HubState`, meta-progression menu, outside runs)
- Framed as a "laboratory / evolution chamber" — arcade-style but a calmer palette than in-run HUD (this is the "prep room" between attempts).
- Central visual: an **evolution tree/map** laid out left-to-right or as a branching path, mirroring the 5-era progression — nodes represent unlockable weapons/accessories and permanent stat upgrades, grouped/colored by which era they belong to. Locked nodes are greyed out with a lock icon; affordable nodes glow; owned/maxed nodes show a filled/checked state.
- Side panel: Evolution Points (meta currency) balance prominently displayed, plus buttons for "Start Run", "Statistics" (best era reached, total runs, playtime), and "Settings".
- Selecting a node opens a small popup card with its cost, current level, and effect description, with a big arcade-style "UPGRADE" button.

### 9f. Main Menu / Pause / Game Over / Victory
- **Main Menu:** Game logo (arcade marquee style, bold pixel font with a glow/chromatic-aberration flicker), big "START", "HUB / LABORATORY", "SETTINGS", "QUIT" buttons stacked vertically, animated background showing a slow pan across a collage of the 5 era backgrounds.
- **Pause:** Simple dark overlay, centered "PAUSED" text, Resume/Settings/Quit-to-Hub options, current build slots shown small on the side for reference.
- **Game Over:** Dramatic but quick — show era reached, run time, enemies killed, Evolution Points earned this run (count up animation), then "Retry" / "Back to Hub" buttons. Keep it snappy, don't over-block the player from immediately trying again (that's a core roguelite retention lever).
- **Victory (all 5 eras cleared):** Bigger celebratory version of Game Over — full stats recap, a special "run completed" banner, still funnels back into the Hub so the player can start a fresh (harder/faster) run afterward.

### 9g. Fonts & Audio-Visual Polish for UI
- Use a bold, blocky pixel font (e.g. something in the style of "Press Start 2P") for all UI text; keep body/description text in a slightly more readable but still blocky secondary pixel font if needed for longer strings (card descriptions).
- Every UI interaction (hover, select, confirm, era transition) should have a short arcade-style sound effect (blips/beeps/power-up jingles) — even placeholder beep tones are fine early on, per Section 8.
- Card/button selection should have a snappy scale+glow animation (no slow easing — arcade UIs feel punchy and immediate, not smooth/corporate).

## 10. STYLE/FEEL NOTES

- The game should feel **challenging and satisfying** — it should create a "let me try just one more run" pull (classic roguelite hook).
- Visual feedback matters: screen reddening/shake on taking damage, explosion effect on enemy death, a glow effect on level-up.
- The final boss (Space Era — Godlike Entity) should feel genuinely epic: large size, multi-phase fight (e.g. 3 phases at 100-66-33-0% health, each phase with a different attack pattern), screen-covering projectile/area attacks (bullet-hell influence is acceptable here).

---

**Final instruction to Fable:** Using the design above, write the code step by step following the MVP order in Section 8, leaving a working/testable state after each step. Use simple placeholder shapes only in the earliest steps as noted — as soon as a system is confirmed working, replace visuals with real sprites sourced per Section 2a, and apply the UI/UX design from Section 9 (era-reactive theme, HUD layout, and screen designs) once the corresponding state is functional. Solidify the mechanics first, then layer in the art and UI polish.
