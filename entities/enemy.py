import math
import random

import pygame
from pygame.math import Vector2

from entities.projectile import Projectile

ARENA = pygame.Rect(0, 0, 1280, 720)


class Enemy:
    _next_id = 0

    def __init__(self, eid, data, pos, hp_scale=1.0, elite=False):
        Enemy._next_id += 1
        self.uid = Enemy._next_id
        self.eid = eid
        self.data = data
        self.pos = Vector2(pos)
        self.elite = elite
        mult_hp = 4.5 if elite else 1.0
        self.max_hp = data["hp"] * hp_scale * mult_hp
        self.hp = self.max_hp
        self.speed = data["speed"] * (1.05 if elite else 1.0) * random.uniform(0.92, 1.08)
        self.damage = data["damage"] * (1.8 if elite else 1.0)
        self.radius = data["radius"] * (1.4 if elite else 1.0)
        self.behavior = data.get("behavior", "chase")
        self.dead = False
        self.contact_cd = 0.0
        self.hit_flash = 0.0
        # dart behavior state
        self._phase = "cruise"
        self._phase_t = random.uniform(0.3, 1.0)
        self._dash_dir = Vector2(0, 0)
        # ranged behavior state
        self._shot_t = random.uniform(0.5, data.get("shot_cd", 2.0))
        self.knockback = Vector2(0, 0)

    def update(self, dt, run):
        player = run.player
        to_p = player.pos - self.pos
        dist = to_p.length()
        direction = to_p / dist if dist > 1 else Vector2(0, 0)

        if self.behavior == "dart":
            self._phase_t -= dt
            if self._phase == "cruise":
                self.pos += direction * self.speed * 0.55 * dt
                if self._phase_t <= 0:
                    self._phase, self._phase_t = "windup", 0.35
            elif self._phase == "windup":
                self._dash_dir = direction
                if self._phase_t <= 0:
                    self._phase, self._phase_t = "dash", 0.4
            else:  # dash
                self.pos += self._dash_dir * self.speed * 2.9 * dt
                if self._phase_t <= 0:
                    self._phase, self._phase_t = "cruise", random.uniform(0.8, 1.4)
        elif self.behavior == "ranged":
            keep = self.data.get("keep_range", 260)
            if dist > keep:
                self.pos += direction * self.speed * dt
            elif dist < keep * 0.7:
                self.pos -= direction * self.speed * 0.7 * dt
            self._shot_t -= dt
            if self._shot_t <= 0 and dist < keep * 1.6:
                self._shot_t = self.data.get("shot_cd", 2.0)
                spd = self.data.get("shot_speed", 260)
                run.enemy_projectiles.append(Projectile(
                    self.pos, direction * spd, self.data.get("shot_damage", 10),
                    ttl=3.0, color=(255, 120, 90), radius=5, from_enemy=True))
        else:  # chase
            self.pos += direction * self.speed * dt

        if self.knockback.length_squared() > 4:
            self.pos += self.knockback * dt
            self.knockback *= max(0.0, 1 - 8 * dt)

        self.pos.x = max(-60, min(ARENA.width + 60, self.pos.x))
        self.pos.y = max(-60, min(ARENA.height + 60, self.pos.y))

        self.contact_cd -= dt
        self.hit_flash = max(0.0, self.hit_flash - dt)
        if dist < self.radius + player.radius and self.contact_cd <= 0:
            self.contact_cd = 0.8
            player.take_damage(self.damage)

    def draw(self, surf, assets):
        size = int(self.radius * 2.4)
        spr = assets.sprite(self.data.get("sprite", self.eid), size)
        rect = spr.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        if self.hit_flash > 0:
            flash = spr.copy()
            flash.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_ADD)
            surf.blit(flash, rect)
        else:
            surf.blit(spr, rect)
        if self.elite:
            pulse = 2 + int(math.sin(pygame.time.get_ticks() * 0.01) * 2)
            pygame.draw.circle(surf, (255, 210, 80), rect.center, int(self.radius) + 4 + pulse, 2)
        if self.behavior == "dart" and self._phase == "windup":
            pygame.draw.circle(surf, (255, 80, 80), rect.center, int(self.radius) + 3, 2)
        # small hp bar when damaged
        if self.hp < self.max_hp:
            w = int(self.radius * 2)
            x, y = int(self.pos.x - w / 2), int(self.pos.y - self.radius - 8)
            pygame.draw.rect(surf, (20, 10, 12), (x, y, w, 4))
            pygame.draw.rect(surf, (230, 70, 70), (x, y, max(1, int(w * self.hp / self.max_hp)), 4))
