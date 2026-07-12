"""Automatic weapons (Vampire Survivors style): the player never aims."""
import math
import random

from pygame.math import Vector2

from entities.particles import Lightning
from entities.projectile import Projectile

MAX_LEVEL = 8


class Weapon:
    def __init__(self, data):
        self.data = data
        self.id = data["id"]
        self.level = 1
        self.timer = random.uniform(0.1, 0.6)
        self.orb_angle = random.uniform(0, math.tau)
        self.hit_cds = {}      # enemy uid -> cooldown remaining (orbit)
        self.aura_pulse = 0.0

    # -- per-level scaling ------------------------------------------------
    @property
    def damage(self):
        return self.data["damage"] * (1 + 0.18 * (self.level - 1))

    @property
    def cooldown(self):
        return self.data.get("cooldown", 1.0) * (0.94 ** (self.level - 1))

    @property
    def count(self):
        return self.data.get("count", 1) + (self.level - 1) // 3

    @property
    def radius(self):
        return self.data.get("radius", 80) * (1 + 0.06 * (self.level - 1))

    def stat_summary(self):
        b = self.data["behavior"]
        if b == "aura":
            return "DMG %d  AREA %d" % (self.damage, self.radius)
        if b == "orbit":
            return "DMG %d  ORBS %d" % (self.damage, self.count)
        if b == "chain":
            return "DMG %d  CHAINS %d" % (self.damage, self.data.get("chain", 3) + (self.level - 1) // 2)
        return "DMG %d  x%d" % (self.damage, self.count)

    # ---------------------------------------------------------------------
    def update(self, dt, run, player):
        behavior = self.data["behavior"]
        if behavior == "orbit":
            self._update_orbit(dt, run, player)
            return
        self.timer -= dt
        if self.timer > 0:
            return
        fired = getattr(self, "_fire_" + behavior)(run, player)
        if fired:
            self.timer = self.cooldown * player.cooldown_mult
            if behavior != "aura":
                run.audio.play("shoot")
        else:
            self.timer = 0.1  # nothing in range: retry soon

    def _dmg(self, player):
        return self.damage * player.damage_mult

    def _spawn(self, run, player, direction):
        d = self.data
        run.projectiles.append(Projectile(
            player.pos, direction * d.get("speed", 400), self._dmg(player),
            ttl=d.get("range", 400) / max(1, d.get("speed", 400)),
            color=d.get("color", (255, 255, 255)), radius=5 + self.level // 3,
            pierce=d.get("pierce", 0) + (1 if self.level >= 5 else 0),
            homing=d.get("homing", False), aoe=d.get("aoe", 0)))

    # -- behaviors ----------------------------------------------------------
    def _fire_nearest(self, run, player):
        rng = self.data.get("range", 400)
        targets = self._nearest_enemies(run, player, rng, self.count)
        if not targets:
            return False
        for i in range(self.count):
            t = targets[i % len(targets)]
            direction = (t.pos - player.pos)
            direction = direction.normalize() if direction.length_squared() > 1 else Vector2(1, 0)
            self._spawn(run, player, direction)
        return True

    def _fire_spread(self, run, player):
        rng = self.data.get("range", 400)
        targets = self._nearest_enemies(run, player, rng, 1)
        if not targets:
            return False
        base = (targets[0].pos - player.pos)
        base = base.normalize() if base.length_squared() > 1 else Vector2(1, 0)
        spread = self.data.get("spread", 20)
        n = self.count
        for i in range(n):
            off = (i - (n - 1) / 2) * spread / max(1, n - 1) * 2 if n > 1 else 0
            self._spawn(run, player, base.rotate(off))
        return True

    def _fire_nova(self, run, player):
        if not run.enemies:
            return False
        n = self.count
        start = random.uniform(0, math.tau)
        for i in range(n):
            a = start + i / n * math.tau
            self._spawn(run, player, Vector2(math.cos(a), math.sin(a)))
        return True

    def _fire_aura(self, run, player):
        r = self.radius
        hit_any = False
        for e in run.enemies:
            if e.pos.distance_squared_to(player.pos) < (r + e.radius) ** 2:
                run.damage_enemy(e, self._dmg(player))
                hit_any = True
        self.aura_pulse = 0.25
        run.aura_ring(player.pos, r, self.data.get("color", (120, 255, 160)))
        return True  # aura always cycles

    def _fire_chain(self, run, player):
        rng = self.data.get("range", 420)
        first = self._nearest_enemies(run, player, rng, 1)
        if not first:
            return False
        chains = self.data.get("chain", 3) + (self.level - 1) // 2
        chain_rng = self.data.get("chain_range", 220)
        points = [Vector2(player.pos)]
        hit = set()
        cur = first[0]
        for _ in range(chains):
            points.append(Vector2(cur.pos))
            hit.add(cur.uid)
            run.damage_enemy(cur, self._dmg(player))
            nxt = None
            best = chain_rng ** 2
            for e in run.enemies:
                if e.uid in hit or e.dead:
                    continue
                d = e.pos.distance_squared_to(cur.pos)
                if d < best:
                    best, nxt = d, e
            if nxt is None:
                break
            cur = nxt
        run.effects.append(Lightning(points, self.data.get("color", (120, 240, 255))))
        return True

    def _update_orbit(self, dt, run, player):
        self.orb_angle += self.data.get("orbit_speed", 3.0) * dt * (1 + 0.05 * (self.level - 1))
        r = self.radius
        n = self.count
        hit_cd = self.data.get("hit_cd", 0.45)
        for uid in list(self.hit_cds):
            self.hit_cds[uid] -= dt
            if self.hit_cds[uid] <= 0:
                del self.hit_cds[uid]
        self.orb_positions = []
        for i in range(n):
            a = self.orb_angle + i / n * math.tau
            op = player.pos + Vector2(math.cos(a), math.sin(a)) * r
            self.orb_positions.append(op)
            for e in run.enemies:
                if e.uid in self.hit_cds or e.dead:
                    continue
                if e.pos.distance_squared_to(op) < (e.radius + 14) ** 2:
                    run.damage_enemy(e, self._dmg(player))
                    self.hit_cds[e.uid] = hit_cd

    # ---------------------------------------------------------------------
    @staticmethod
    def _nearest_enemies(run, player, rng, count):
        in_range = [(e.pos.distance_squared_to(player.pos), e.uid, e) for e in run.enemies
                    if e.pos.distance_squared_to(player.pos) < rng * rng]
        in_range.sort()
        return [e for _, _, e in in_range[:count]]

    def draw(self, surf, player):
        import pygame
        if self.data["behavior"] == "orbit":
            for op in getattr(self, "orb_positions", []):
                c = self.data.get("color", (255, 255, 255))
                pygame.draw.circle(surf, c, (int(op.x), int(op.y)), 9)
                pygame.draw.circle(surf, (255, 255, 255), (int(op.x), int(op.y)), 4)
        elif self.data["behavior"] == "aura" and self.aura_pulse > 0:
            self.aura_pulse -= 1 / 60
