import pygame
from pygame.math import Vector2

COLORS = {
    "xp": (110, 220, 255),
    "energy": (255, 220, 90),
    "health": (110, 255, 130),
    "evo": (230, 130, 255),
}
RADII = {"xp": 5, "energy": 6, "health": 7, "evo": 8}


class Pickup:
    __slots__ = ("pos", "kind", "value", "vel", "dead", "bob")

    def __init__(self, pos, kind, value):
        self.pos = Vector2(pos)
        self.kind = kind
        self.value = value
        self.vel = Vector2(0, 0)
        self.dead = False
        self.bob = 0.0

    def update(self, dt, run):
        player = run.player
        self.bob += dt * 6
        d = player.pos - self.pos
        dist_sq = d.length_squared()
        attract = player.pickup_radius if self.kind != "evo" else player.pickup_radius * 2.5
        if dist_sq < attract * attract and dist_sq > 1:
            self.vel += d.normalize() * 1600 * dt
            if self.vel.length() > 620:
                self.vel.scale_to_length(620)
        else:
            self.vel *= max(0.0, 1 - 6 * dt)
        self.pos += self.vel * dt
        if dist_sq < (player.radius + 10) ** 2:
            self.dead = True
            run.collect_pickup(self)

    ICON_KEYS = {"xp": "xp_gem", "energy": "energy", "health": "heal", "evo": "evo"}

    def draw(self, surf, assets):
        import math
        r = RADII[self.kind]
        size = r * 2 + 4 + (2 if math.sin(self.bob) > 0 else 0)
        p = (int(self.pos.x), int(self.pos.y))
        pygame.draw.circle(surf, (10, 10, 16, 120), p, r + 3)  # grounding shadow
        icon = assets.icon(self.ICON_KEYS[self.kind], COLORS[self.kind], size)
        surf.blit(icon, icon.get_rect(center=p))
