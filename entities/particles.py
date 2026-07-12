"""Lightweight particles, floating damage numbers and lightning flashes."""
import random

import pygame
from pygame.math import Vector2


class Particle:
    __slots__ = ("pos", "vel", "life", "max_life", "color", "size", "dead")

    def __init__(self, pos, vel, life, color, size):
        self.pos = Vector2(pos)
        self.vel = Vector2(vel)
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.dead = False

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            self.dead = True
            return
        self.pos += self.vel * dt
        self.vel *= max(0.0, 1 - 3 * dt)

    def draw(self, surf):
        f = self.life / self.max_life
        s = max(1, int(self.size * f))
        pygame.draw.circle(surf, self.color, (int(self.pos.x), int(self.pos.y)), s)


def burst(particles, pos, color, count=10, speed=180, life=0.45, size=4):
    for _ in range(count):
        ang = random.uniform(0, 6.283)
        spd = random.uniform(speed * 0.3, speed)
        vel = (Vector2(1, 0).rotate_rad(ang)) * spd
        particles.append(Particle(pos, vel, random.uniform(life * 0.5, life), color, size))


class DamageText:
    __slots__ = ("pos", "text", "color", "life", "dead", "big")

    def __init__(self, pos, text, color, big=False):
        self.pos = Vector2(pos) + (random.uniform(-8, 8), -10)
        self.text = text
        self.color = color
        self.life = 0.7
        self.dead = False
        self.big = big

    def update(self, dt):
        self.life -= dt
        self.pos.y -= 55 * dt
        if self.life <= 0:
            self.dead = True

    def draw(self, surf, fonts):
        font = fonts["body"] if self.big else fonts["small"]
        alpha = int(255 * min(1.0, self.life / 0.4))
        pos = (int(self.pos.x), int(self.pos.y))
        dark = font.render(self.text, False, (10, 10, 14))
        dark.set_alpha(alpha)
        rect = dark.get_rect(center=pos)
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            surf.blit(dark, rect.move(dx, dy))
        img = font.render(self.text, False, self.color)
        img.set_alpha(alpha)
        surf.blit(img, rect)


class Lightning:
    """Instant chain-lightning flash drawn for a fraction of a second."""
    __slots__ = ("points", "life", "color", "dead")

    def __init__(self, points, color):
        self.points = points
        self.life = 0.15
        self.color = color
        self.dead = False

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            self.dead = True

    def draw(self, surf):
        if len(self.points) < 2:
            return
        pts = [(int(p.x), int(p.y)) for p in self.points]
        pygame.draw.lines(surf, (255, 255, 255), False, pts, 4)
        pygame.draw.lines(surf, self.color, False, pts, 2)
