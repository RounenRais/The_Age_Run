import pygame
from pygame.math import Vector2


class Projectile:
    __slots__ = ("pos", "vel", "damage", "pierce", "ttl", "color", "radius",
                 "homing", "aoe", "from_enemy", "dead", "hit_ids")

    def __init__(self, pos, vel, damage, ttl, color, radius=5, pierce=0,
                 homing=False, aoe=0, from_enemy=False):
        self.pos = Vector2(pos)
        self.vel = Vector2(vel)
        self.damage = damage
        self.pierce = pierce
        self.ttl = ttl
        self.color = color
        self.radius = radius
        self.homing = homing
        self.aoe = aoe
        self.from_enemy = from_enemy
        self.dead = False
        self.hit_ids = set()

    def update(self, dt, run):
        self.ttl -= dt
        if self.ttl <= 0:
            self.dead = True
            return
        if self.homing and not self.from_enemy and run.enemies:
            target = min(run.enemies, key=lambda e: e.pos.distance_squared_to(self.pos))
            desired = (target.pos - self.pos)
            if desired.length_squared() > 1:
                desired = desired.normalize() * self.vel.length()
                self.vel += (desired - self.vel) * min(1.0, 4.5 * dt)
        self.pos += self.vel * dt

    def draw(self, surf):
        p = (int(self.pos.x), int(self.pos.y))
        glow = tuple(min(255, c + 60) for c in self.color)
        pygame.draw.circle(surf, self.color, p, self.radius)
        pygame.draw.circle(surf, glow, p, max(1, self.radius - 2))
