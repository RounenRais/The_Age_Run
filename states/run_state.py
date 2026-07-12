"""The actual game: waves, combat, XP, level-up overlay, era flow."""
import math
import random

import pygame
from pygame.math import Vector2

from entities import particles
from entities.boss import Boss
from entities.enemy import Enemy
from entities.pickup import Pickup
from entities.player import Player
from states.state import State
from systems.spawner import Spawner, edge_position
from systems.weapons import Weapon, MAX_LEVEL
from ui import theme as thm
from ui.hud import draw_hud
from ui.widgets import Card

W, H = 1280, 720
BOSS_EVO = [20, 35, 55, 80, 120]        # evolution points per era boss
WAVE_EVO_BASE = 2
MAX_ACC_LEVEL = 5


class RunState(State):
    def enter(self, new_run=False, advance_era=False, resume=False):
        if new_run:
            self._start_new_run()
        elif advance_era:
            self._advance_era()
        # resume: nothing to do

    # ------------------------------------------------------------------
    def _start_new_run(self):
        g = self.game
        self.era = 0
        self.time = 0.0
        self.energy = 0
        self.evo_earned = 0
        self.kills = 0
        self.player = Player(g, self)
        start = next(w for w in g.data["weapons"] if w["id"] == "pseudopod")
        self.player.weapons.append(Weapon(start))
        self._setup_era()
        self.pending_levelups = 0
        self.levelup_cards = None
        self.audio.play("era")

    def _advance_era(self):
        self.era += 1
        self.player.heal(self.player.max_hp)  # fresh era, fresh start
        self._setup_era()
        self.audio.play("era")

    def _setup_era(self):
        g = self.game
        era_data = g.data["eras"][self.era]
        self.theme = thm.Theme(era_data["palette"])
        self.spawner = Spawner(era_data, self.era)
        self.enemies = []
        self.boss = None
        self.projectiles = []
        self.enemy_projectiles = []
        self.pickups = []
        self.particles = []
        self.damage_texts = []
        self.effects = []
        self.zones = []
        self.rings = []            # aura pulse rings [x, y, r, max_r, color, t]
        self.shake_t = 0.0
        self.vignette_t = 0.0
        self.banner_t = 3.0
        self.banner_text = era_data["name"]
        self.event_text = ""
        self.event_t = 0.0
        self._bg = self._make_background(era_data)
        self._world = pygame.Surface((W, H))

    def _make_background(self, era_data):
        rng = random.Random(era_data["id"])
        bg = pygame.Surface((W, H))
        bg.fill(era_data["bg_color"])
        base = era_data["bg_color"]
        for _ in range(70):  # scattered dim texture blobs
            c = tuple(min(255, v + rng.randint(4, 14)) for v in base)
            pygame.draw.circle(bg, c, (rng.randint(0, W), rng.randint(0, H)), rng.randint(2, 26))
        grid_c = tuple(min(255, v + 7) for v in base)
        for x in range(0, W, 64):
            pygame.draw.line(bg, grid_c, (x, 0), (x, H))
        for y in range(0, H, 64):
            pygame.draw.line(bg, grid_c, (0, y), (W, y))
        return bg

    @property
    def audio(self):
        return self.game.audio

    # ------------------------------------------------------------------
    # spawning / drops
    # ------------------------------------------------------------------
    def spawn_enemy(self, eid, near=None, elite=False, hp_scale=None):
        data = self.game.data["enemies"][eid]
        if near is not None:
            pos = Vector2(near) + Vector2(random.uniform(-70, 70), random.uniform(-70, 70))
        else:
            pos = edge_position()
        scale = hp_scale if hp_scale is not None else self.spawner.hp_scale()
        self.enemies.append(Enemy(eid, data, pos, hp_scale=scale, elite=elite))

    def spawn_boss(self, boss_id):
        data = self.game.data["enemies"][boss_id]
        pos = edge_position()
        self.boss = Boss(boss_id, data, pos)
        self.enemies.append(self.boss)
        self.audio.play("boss_roar")
        self.boss_event(data["name"] + " APPROACHES!")
        self.shake(0.5)

    def boss_event(self, text):
        self.event_text = text
        self.event_t = 2.2

    def damage_enemy(self, enemy, dmg):
        if enemy.dead:
            return
        crit = random.random() < self.player.crit
        if crit:
            dmg *= 2
        enemy.hp -= dmg
        enemy.hit_flash = 0.08
        color = (255, 180, 60) if crit else (240, 240, 240)
        if len(self.damage_texts) < 60:
            self.damage_texts.append(particles.DamageText(enemy.pos, str(int(dmg)), color, big=crit))
        if enemy.hp <= 0:
            self._kill_enemy(enemy)

    def _kill_enemy(self, enemy):
        enemy.dead = True
        self.kills += 1
        pos = Vector2(enemy.pos)
        d = enemy.data
        particles.burst(self.particles, pos, self.theme.accent, count=8, speed=160)
        self.audio.play("hit")
        # drops
        self.pickups.append(Pickup(pos, "xp", d["xp"]))
        if random.random() < 0.55:
            self.pickups.append(Pickup(pos + (random.uniform(-8, 8), random.uniform(-8, 8)),
                                       "energy", d["energy"]))
        if random.random() < 0.03:
            self.pickups.append(Pickup(pos, "health", 15 + 10 * self.era))
        if enemy.elite:
            self.pickups.append(Pickup(pos, "evo", 3 + self.era * 2))
            particles.burst(self.particles, pos, (255, 210, 80), count=18, speed=240)
        if getattr(enemy, "eid", "") and d.get("boss"):
            self._on_boss_killed(enemy)

    def _on_boss_killed(self, boss):
        self.audio.play("boss_die")
        self.shake(0.8)
        particles.burst(self.particles, boss.pos, (255, 255, 255), count=40, speed=380, life=0.9, size=6)
        base = BOSS_EVO[self.era]
        time_bonus = max(0, 10 - int(self.time / 300))  # faster runs pay a little more
        self.award_evo(base + time_bonus)
        self.energy += int(boss.data["energy"] * self.player.energy_mult)
        self.spawner.done = True
        self.boss = None
        # clear the field
        for e in self.enemies:
            if not e.dead:
                e.dead = True
                self.pickups.append(Pickup(e.pos, "xp", e.data["xp"]))
        if self.era >= len(self.game.data["eras"]) - 1:
            self._finish_run(victory=True)
        else:
            self.game.change_state("build_select", run=self)

    def award_evo(self, amount):
        self.evo_earned += int(round(amount * self.player.evo_mult))

    def on_wave_complete(self, wave_index):
        self.award_evo(WAVE_EVO_BASE + self.era * 2)
        self.energy += int((8 + self.era * 6) * self.player.energy_mult)
        self.audio.play("confirm")

    # ------------------------------------------------------------------
    # pickups / xp / level-ups
    # ------------------------------------------------------------------
    def collect_pickup(self, pk):
        if pk.kind == "xp":
            self.audio.play("pickup")
            self.player.gain_xp(pk.value)
        elif pk.kind == "energy":
            self.audio.play("energy")
            self.energy += int(round(pk.value * self.player.energy_mult))
        elif pk.kind == "health":
            self.player.heal(pk.value)
        elif pk.kind == "evo":
            self.award_evo(pk.value)
            self.audio.play("buy")

    def queue_levelups(self, count):
        self.pending_levelups += count

    def _open_levelup(self):
        self.audio.play("levelup")
        options = self._levelup_options()
        cards = []
        cw, ch = 260, 300
        total = len(options)
        x0 = W // 2 - (total * cw + (total - 1) * 30) // 2
        for i, opt in enumerate(options):
            rect = pygame.Rect(x0 + i * (cw + 30), H // 2 - ch // 2, cw, ch)
            card = Card(rect, opt["title"], opt["lines"], icon=opt["icon"],
                        accent=opt.get("accent"), footer="[%d]" % (i + 1))
            card.action = opt["action"]
            cards.append(card)
        self.levelup_cards = cards

    def _levelup_options(self):
        g, p = self.game, self.player
        assets = g.assets
        pool = []

        for w in p.weapons:
            if w.level < MAX_LEVEL:
                pool.append((3.0, {
                    "title": w.data["name"] + " +",
                    "lines": ["Level %d -> %d" % (w.level, w.level + 1), w.stat_summary()],
                    "icon": assets.icon(w.id, w.data["color"], 52, fallback=w.data["behavior"]),
                    "accent": tuple(w.data["color"]),
                    "action": ("weapon_up", w)}))

        if len(p.weapons) < p.weapon_slots:
            owned = {w.id for w in p.weapons}
            for wd in g.data["weapons"]:
                if wd["id"] in owned or wd["era"] > self.era:
                    continue
                if wd.get("locked") and not g.save.is_unlocked(wd["id"]):
                    continue
                pool.append((2.2, {
                    "title": wd["name"],
                    "lines": ["NEW WEAPON", wd["desc"]],
                    "icon": assets.icon(wd["id"], wd["color"], 52, fallback=wd["behavior"]),
                    "accent": tuple(wd["color"]),
                    "action": ("weapon_new", wd)}))

        for ad in g.data["accessories"]:
            if ad["era"] > self.era:
                continue
            lvl = p.accessories.get(ad["id"], 0)
            if lvl >= MAX_ACC_LEVEL or (lvl == 0 and len(p.accessories) >= p.acc_slots):
                continue
            pool.append((2.0, {
                "title": ad["name"],
                "lines": [("NEW PASSIVE" if lvl == 0 else "Level %d -> %d" % (lvl, lvl + 1)), ad["desc"]],
                "icon": assets.icon(ad["stat"], self.theme.accent, 52, fallback="accessory"),
                "action": ("accessory", ad)}))

        pool.append((0.8, {
            "title": "Regenerate",
            "lines": ["Heal 40% of Max HP"],
            "icon": assets.icon("heal", (110, 255, 130), 52),
            "accent": (110, 255, 130),
            "action": ("heal", None)}))

        options = []
        while pool and len(options) < 3:
            weights = [w for w, _ in pool]
            idx = random.choices(range(len(pool)), weights=weights)[0]
            options.append(pool.pop(idx)[1])
        return options

    def _apply_levelup(self, action):
        kind, payload = action
        p = self.player
        if kind == "weapon_up":
            payload.level += 1
        elif kind == "weapon_new":
            p.weapons.append(Weapon(payload))
        elif kind == "accessory":
            p.add_accessory(payload)
        elif kind == "heal":
            p.heal(p.max_hp * 0.4)
        self.audio.play("confirm")
        self.levelup_cards = None
        self.pending_levelups -= 1

    # ------------------------------------------------------------------
    # feedback hooks
    # ------------------------------------------------------------------
    def shake(self, t):
        self.shake_t = max(self.shake_t, t)

    def on_player_hit(self, dmg):
        self.vignette_t = 0.35
        self.shake(0.25)
        self.audio.play("hurt")

    def on_player_revive(self):
        self.boss_event("SECOND GENESIS!")
        self.audio.play("levelup")
        for e in self.enemies:  # knock everything back
            d = e.pos - self.player.pos
            if 0 < d.length() < 350:
                e.knockback = d.normalize() * 900

    def on_player_death(self):
        self._finish_run(victory=False)

    def _finish_run(self, victory):
        g = self.game
        g.save.evo += self.evo_earned
        g.save.record_run(self.era + 1, self.kills, self.time, victory)
        stats = {
            "era": self.era, "time": self.time, "kills": self.kills,
            "evo": self.evo_earned, "level": self.player.level,
        }
        snapshot = g.screen.copy()
        g.change_state("victory" if victory else "game_over", stats=stats, bg=snapshot)

    def zone_detonated(self, zone):
        particles.burst(self.particles, zone.pos, (255, 140, 60), count=14, speed=260)
        self.shake(0.15)

    def aura_ring(self, pos, radius, color):
        if len(self.rings) < 12:
            self.rings.append([pos.x, pos.y, radius * 0.4, radius, color, 0.25])

    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.change_state("pause", bg=self.game.screen.copy())
            return
        if self.levelup_cards:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                idx = event.key - pygame.K_1
                if idx < len(self.levelup_cards):
                    self._apply_levelup(self.levelup_cards[idx].action)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for c in self.levelup_cards:
                    if c.rect.collidepoint(event.pos):
                        self._apply_levelup(c.action)
                        break

    # ------------------------------------------------------------------
    def update(self, dt):
        if self.levelup_cards:
            mp = pygame.mouse.get_pos()
            for c in self.levelup_cards:
                c.update_hover(mp, self.audio)
            return
        if self.pending_levelups > 0:
            self._open_levelup()
            return

        self.time += dt
        self.player.update(dt)
        self.spawner.update(dt, self)

        for e in self.enemies:
            e.update(dt, self)
        for pr in self.projectiles:
            pr.update(dt, self)
        for pr in self.enemy_projectiles:
            pr.update(dt, self)
        for pk in self.pickups:
            pk.update(dt, self)
        for z in self.zones:
            z.update(dt, self)
        for pt in self.particles:
            pt.update(dt)
        for dtx in self.damage_texts:
            dtx.update(dt)
        for fx in self.effects:
            fx.update(dt)
        for ring in self.rings:
            ring[5] -= dt
            ring[2] += (ring[3] - ring[2]) * 10 * dt

        self._collide(dt)

        self.enemies = [e for e in self.enemies if not e.dead]
        self.projectiles = [p for p in self.projectiles if not p.dead]
        self.enemy_projectiles = [p for p in self.enemy_projectiles if not p.dead]
        self.pickups = [p for p in self.pickups if not p.dead]
        self.zones = [z for z in self.zones if not z.dead]
        self.particles = [p for p in self.particles if not p.dead]
        self.damage_texts = [d for d in self.damage_texts if not d.dead]
        self.effects = [f for f in self.effects if not f.dead]
        self.rings = [r for r in self.rings if r[5] > 0]

        self.shake_t = max(0.0, self.shake_t - dt)
        self.vignette_t = max(0.0, self.vignette_t - dt)
        self.banner_t = max(0.0, self.banner_t - dt)
        self.event_t = max(0.0, self.event_t - dt)

    def _collide(self, dt):
        # player projectiles vs enemies
        for pr in self.projectiles:
            if pr.dead:
                continue
            for e in self.enemies:
                if e.dead or e.uid in pr.hit_ids:
                    continue
                r = e.radius + pr.radius
                if e.pos.distance_squared_to(pr.pos) < r * r:
                    if pr.aoe:
                        self._explode(pr)
                        pr.dead = True
                        break
                    self.damage_enemy(e, pr.damage)
                    pr.hit_ids.add(e.uid)
                    if pr.pierce <= 0:
                        pr.dead = True
                        break
                    pr.pierce -= 1
        # enemy projectiles vs player
        p = self.player
        for pr in self.enemy_projectiles:
            if pr.dead:
                continue
            r = p.radius + pr.radius
            if p.pos.distance_squared_to(pr.pos) < r * r:
                pr.dead = True
                p.take_damage(pr.damage)

    def _explode(self, pr):
        particles.burst(self.particles, pr.pos, (255, 190, 90), count=16, speed=300, life=0.5, size=5)
        self.audio.play("explosion")
        self.shake(0.12)
        for e in self.enemies:
            if not e.dead and e.pos.distance_squared_to(pr.pos) < (pr.aoe + e.radius) ** 2:
                self.damage_enemy(e, pr.damage)

    # ------------------------------------------------------------------
    def draw(self, surf):
        world = self._world
        world.blit(self._bg, (0, 0))

        for ring in self.rings:
            alpha_surf = pygame.Surface((int(ring[3] * 2 + 4), int(ring[3] * 2 + 4)), pygame.SRCALPHA)
            pygame.draw.circle(alpha_surf, (*ring[4], int(140 * ring[5] / 0.25)),
                               (int(ring[3] + 2), int(ring[3] + 2)), int(ring[2]), 3)
            world.blit(alpha_surf, (ring[0] - ring[3] - 2, ring[1] - ring[3] - 2))

        for z in self.zones:
            z.draw(world)
        for pk in self.pickups:
            pk.draw(world, self.game.assets)
        for e in self.enemies:
            e.draw(world, self.game.assets)
        for w in self.player.weapons:
            w.draw(world, self.player)
        self.player.draw(world, self.game.assets, self.era)
        for pr in self.projectiles:
            pr.draw(world)
        for pr in self.enemy_projectiles:
            pr.draw(world)
        for fx in self.effects:
            fx.draw(world)
        for pt in self.particles:
            pt.draw(world)
        for dtx in self.damage_texts:
            dtx.draw(world, self.game.fonts)

        off = (0, 0)
        if self.shake_t > 0:
            amp = 8 * self.shake_t
            off = (random.uniform(-amp, amp), random.uniform(-amp, amp))
        surf.fill((0, 0, 0))
        surf.blit(world, off)

        if self.vignette_t > 0:
            vd = pygame.Surface((W, H), pygame.SRCALPHA)
            a = int(120 * self.vignette_t / 0.35)
            pygame.draw.rect(vd, (200, 20, 20, a), (0, 0, W, H), 26)
            surf.blit(vd, (0, 0))

        draw_hud(surf, self)

        if self.banner_t > 0:
            a = int(255 * min(1.0, self.banner_t / 0.6))
            for color, off, alpha in (((10, 10, 14), 3, a), (self.theme.accent, 0, a)):
                img = self.game.fonts["huge"].render(self.banner_text, False, color)
                img.set_alpha(alpha)
                surf.blit(img, img.get_rect(center=(W // 2 + off, H // 3 + off)))
        if self.event_t > 0:
            a = int(255 * min(1.0, self.event_t / 0.5))
            for color, off in (((10, 10, 14), 2), ((255, 170, 120), 0)):
                img = self.game.fonts["med"].render(self.event_text, False, color)
                img.set_alpha(a)
                surf.blit(img, img.get_rect(center=(W // 2 + off, H // 4 + off)))

        if self.levelup_cards:
            dim = pygame.Surface((W, H), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 160))
            surf.blit(dim, (0, 0))
            title = self.game.fonts["big"].render("LEVEL UP!", False, self.theme.accent)
            surf.blit(title, title.get_rect(center=(W // 2, H // 2 - 200)))
            for c in self.levelup_cards:
                c.draw(surf, self.theme, self.game.fonts)
