"""Era bosses with bespoke attack patterns, driven by boss id."""
import math
import random

import pygame
from pygame.math import Vector2

from entities.enemy import Enemy
from entities.projectile import Projectile


class Zone:
    """Telegraphed area attack: shows a warning circle, then detonates."""
    __slots__ = ("pos", "radius", "delay", "damage", "dead", "max_delay")

    def __init__(self, pos, radius, delay, damage):
        self.pos = Vector2(pos)
        self.radius = radius
        self.delay = delay
        self.max_delay = delay
        self.damage = damage
        self.dead = False

    def update(self, dt, run):
        self.delay -= dt
        if self.delay <= 0:
            self.dead = True
            if run.player.pos.distance_squared_to(self.pos) < self.radius ** 2:
                run.player.take_damage(self.damage, ignore_iframes=True)
            run.zone_detonated(self)

    def draw(self, surf):
        f = 1 - self.delay / self.max_delay
        p = (int(self.pos.x), int(self.pos.y))
        pygame.draw.circle(surf, (255, 90, 60), p, int(self.radius), 2)
        pygame.draw.circle(surf, (255, 150, 80), p, max(2, int(self.radius * f)), 2)


class Boss(Enemy):
    def __init__(self, eid, data, pos, hp_scale=1.0):
        super().__init__(eid, data, pos, hp_scale=hp_scale, elite=False)
        self.behavior = "boss"
        self.t = 0.0
        self.attack_t = 2.0
        self.summon_t = 6.0
        self.spiral_a = 0.0
        self.split_done = False
        self.phase = 1
        self.state = "move"       # move / windup / charge
        self.state_t = 0.0
        self.charge_dir = Vector2(1, 0)

    # ------------------------------------------------------------------
    def update(self, dt, run):
        self.t += dt
        self.hit_flash = max(0.0, self.hit_flash - dt)
        self.contact_cd -= dt
        player = run.player
        to_p = player.pos - self.pos
        dist = to_p.length()
        direction = to_p / dist if dist > 1 else Vector2(1, 0)

        handler = getattr(self, "_upd_" + self.eid, None)
        if handler:
            handler(dt, run, player, direction, dist)

        self.pos.x = max(40, min(1240, self.pos.x))
        self.pos.y = max(40, min(680, self.pos.y))

        if dist < self.radius + player.radius and self.contact_cd <= 0:
            self.contact_cd = 0.9
            player.take_damage(self.damage)

    # -- Era 1: splits and floods the arena with spawn ------------------
    def _upd_mother_amoeba(self, dt, run, player, direction, dist):
        speed = self.speed * (1.6 if self.split_done else 1.0)
        self.pos += direction * speed * dt
        self.summon_t -= dt
        if self.summon_t <= 0:
            self.summon_t = 6.0
            for _ in range(3):
                run.spawn_enemy(random.choice(["amoeba", "bacteria"]), near=self.pos)
        if not self.split_done and self.hp < self.max_hp * 0.5:
            self.split_done = True
            run.boss_event("THE AMOEBA SPLITS!")
            for _ in range(4):
                run.spawn_enemy("amoeba", near=self.pos)

    # -- Era 2: telegraphed charges --------------------------------------
    def _upd_alpha_predator(self, dt, run, player, direction, dist):
        self.state_t -= dt
        if self.state == "move":
            self.pos += direction * self.speed * dt
            if self.state_t <= 0:
                self.state, self.state_t = "windup", 0.55
        elif self.state == "windup":
            self.charge_dir = direction
            if self.state_t <= 0:
                self.state, self.state_t = "charge", 0.55
                run.audio.play("boss_roar")
        else:
            self.pos += self.charge_dir * self.speed * 6.0 * dt
            if self.state_t <= 0:
                self.state, self.state_t = "move", random.uniform(1.8, 2.6)
        self.summon_t -= dt
        if self.summon_t <= 0:
            self.summon_t = 8.0
            for _ in range(2):
                run.spawn_enemy("insect", near=self.pos)

    # -- Era 3: keeps range, fire zones, summons packs -------------------
    def _upd_tribal_shaman(self, dt, run, player, direction, dist):
        if dist > 320:
            self.pos += direction * self.speed * dt
        elif dist < 240:
            self.pos -= direction * self.speed * dt
        self.attack_t -= dt
        if self.attack_t <= 0:
            self.attack_t = 2.6
            run.zones.append(Zone(player.pos, 95, 1.1, 34))
            if random.random() < 0.5:
                for i in range(6):
                    a = i / 6 * math.tau
                    vel = Vector2(math.cos(a), math.sin(a)) * 220
                    run.enemy_projectiles.append(Projectile(
                        self.pos, vel, 20, 3.0, (255, 160, 60), 6, from_enemy=True))
        self.summon_t -= dt
        if self.summon_t <= 0:
            self.summon_t = 9.0
            run.boss_event("THE SHAMAN CALLS THE PACK!")
            for _ in range(3):
                run.spawn_enemy("wolf", near=self.pos)

    # -- Era 4: volleys and spiral fire ----------------------------------
    def _upd_war_machine(self, dt, run, player, direction, dist):
        self.pos += direction * self.speed * dt
        self.attack_t -= dt
        if self.attack_t <= 0:
            self.attack_t = 2.2
            if random.random() < 0.55:
                base = math.atan2(direction.y, direction.x)
                for i in range(5):
                    a = base + (i - 2) * 0.16
                    vel = Vector2(math.cos(a), math.sin(a)) * 320
                    run.enemy_projectiles.append(Projectile(
                        self.pos, vel, 26, 3.0, (255, 120, 110), 6, from_enemy=True))
            else:
                for i in range(12):
                    a = self.spiral_a + i / 12 * math.tau
                    vel = Vector2(math.cos(a), math.sin(a)) * 240
                    run.enemy_projectiles.append(Projectile(
                        self.pos, vel, 24, 3.5, (255, 170, 90), 6, from_enemy=True))
                self.spiral_a += 0.35
        self.summon_t -= dt
        if self.summon_t <= 0:
            self.summon_t = 10.0
            for _ in range(2):
                run.spawn_enemy("drone", near=self.pos)

    # -- Era 5: multi-phase bullet hell ----------------------------------
    def _upd_godlike_entity(self, dt, run, player, direction, dist):
        frac = self.hp / self.max_hp
        new_phase = 1 if frac > 0.66 else (2 if frac > 0.33 else 3)
        if new_phase != self.phase:
            self.phase = new_phase
            run.boss_event("THE ENTITY ASCENDS! PHASE %d" % new_phase)
            run.audio.play("boss_roar")
            run.shake(0.6)
            for i in range(20):  # phase-change ring
                a = i / 20 * math.tau
                vel = Vector2(math.cos(a), math.sin(a)) * 200
                run.enemy_projectiles.append(Projectile(
                    self.pos, vel, 30, 4.0, (230, 140, 255), 7, from_enemy=True))

        speed = self.speed * (1 + 0.4 * (self.phase - 1))
        if dist > 200:
            self.pos += direction * speed * dt

        self.attack_t -= dt
        rate = [2.2, 1.5, 1.0][self.phase - 1]
        if self.attack_t <= 0:
            self.attack_t = rate
            if self.phase == 1:
                n = 16
                for i in range(n):
                    a = self.spiral_a + i / n * math.tau
                    vel = Vector2(math.cos(a), math.sin(a)) * 230
                    run.enemy_projectiles.append(Projectile(
                        self.pos, vel, 28, 4.0, (200, 120, 255), 6, from_enemy=True))
                self.spiral_a += 0.4
            elif self.phase == 2:
                base = math.atan2(direction.y, direction.x)
                for i in range(7):
                    a = base + (i - 3) * 0.14
                    vel = Vector2(math.cos(a), math.sin(a)) * 350
                    run.enemy_projectiles.append(Projectile(
                        self.pos, vel, 30, 3.0, (120, 240, 255), 6, from_enemy=True))
                run.zones.append(Zone(player.pos, 110, 1.0, 40))
            else:
                n = 24
                for i in range(n):
                    a = self.spiral_a + i / n * math.tau
                    vel = Vector2(math.cos(a), math.sin(a)) * 260
                    run.enemy_projectiles.append(Projectile(
                        self.pos, vel, 32, 4.0, (255, 120, 200), 6, from_enemy=True))
                self.spiral_a += 0.25
                run.zones.append(Zone(player.pos, 130, 0.9, 45))

        self.summon_t -= dt
        if self.summon_t <= 0 and self.phase >= 2:
            self.summon_t = 8.0
            for _ in range(2):
                run.spawn_enemy("energy_being", near=self.pos)

    # ------------------------------------------------------------------
    def draw(self, surf, assets):
        size = int(self.radius * 2.5)
        wob = 1.0 + 0.04 * math.sin(self.t * 3)
        spr = assets.sprite(self.data.get("sprite", self.eid), int(size * wob))
        rect = spr.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        if self.state == "windup":
            pygame.draw.circle(surf, (255, 70, 70), rect.center, int(self.radius) + 8, 3)
        if self.hit_flash > 0:
            flash = spr.copy()
            flash.fill((200, 200, 200, 0), special_flags=pygame.BLEND_RGBA_ADD)
            surf.blit(flash, rect)
        else:
            surf.blit(spr, rect)
