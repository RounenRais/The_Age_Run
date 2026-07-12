"""Asset loading helper.

Looks for real sprite PNGs under /assets/<category>/<key>.png first; when a
file is missing it falls back to a procedurally drawn stylized sprite so the
game is always playable. Dropping a correctly named PNG into /assets makes it
picked up automatically with no code change (see CLAUDE.md section 2a).
"""
import math
import os
import random

import pygame

ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
CATEGORIES = ["player", "enemies", "bosses", "weapons", "pickups", "ui", "vfx"]


def _darken(c, f=0.5):
    return (int(c[0] * f), int(c[1] * f), int(c[2] * f))


def _lighten(c, f=0.5):
    return (int(c[0] + (255 - c[0]) * f), int(c[1] + (255 - c[1]) * f), int(c[2] + (255 - c[2]) * f))


class AssetLoader:
    def __init__(self):
        self._cache = {}

    def sprite(self, key, size):
        """Return a Surface for `key` scaled to `size` px (largest dimension)."""
        size = int(size)
        ck = (key, size)
        if ck in self._cache:
            return self._cache[ck]
        surf = self._load_file(key)
        if surf is None:
            surf = self._generate(key, size)
        else:
            w, h = surf.get_size()
            scale = size / max(w, h)
            surf = pygame.transform.scale(surf, (max(1, int(w * scale)), max(1, int(h * scale))))
        self._cache[ck] = surf
        return surf

    def _load_file(self, key):
        for cat in CATEGORIES:
            path = os.path.join(ASSET_DIR, cat, key + ".png")
            if os.path.exists(path):
                try:
                    return pygame.image.load(path).convert_alpha()
                except pygame.error:
                    return None
        return None

    # ------------------------------------------------------------------
    # Procedural sprite generation (deterministic per key)
    # ------------------------------------------------------------------
    def _generate(self, key, size):
        rng = random.Random(key)
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        r = size * 0.42

        def blob(color, wobble=0.22, points=12, cx=c, cy=c, rad=r):
            pts = []
            for i in range(points):
                a = i / points * math.tau
                rr = rad * (1 - wobble / 2 + rng.random() * wobble)
                pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
            pygame.draw.polygon(s, _darken(color, 0.45), pts)
            inner = [(cx + (x - cx) * 0.82, cy + (y - cy) * 0.82) for x, y in pts]
            pygame.draw.polygon(s, color, inner)

        def spiky(color, spikes=8, inner_f=0.5):
            pts = []
            for i in range(spikes * 2):
                a = i / (spikes * 2) * math.tau
                rr = r if i % 2 == 0 else r * inner_f
                pts.append((c + math.cos(a) * rr, c + math.sin(a) * rr))
            pygame.draw.polygon(s, _darken(color, 0.5), pts)
            pygame.draw.polygon(s, color, [(c + (x - c) * 0.8, c + (y - c) * 0.8) for x, y in pts])

        def eyes(color=(255, 255, 255), dx=0.3, dy=-0.1, er=None):
            er = er or max(2, size // 10)
            for sx in (-1, 1):
                pygame.draw.circle(s, color, (int(c + sx * r * dx), int(c + r * dy)), er)
                pygame.draw.circle(s, (10, 10, 20), (int(c + sx * r * dx), int(c + r * dy)), max(1, er // 2))

        def humanoid(body, head, weapon_color=None):
            bw, bh = size * 0.44, size * 0.5
            pygame.draw.rect(s, _darken(body, 0.5), (c - bw / 2 - 2, c - 2, bw + 4, bh + 4), border_radius=3)
            pygame.draw.rect(s, body, (c - bw / 2, c, bw, bh), border_radius=3)
            hr = size * 0.2
            pygame.draw.circle(s, _darken(head, 0.6), (c, int(c - hr * 0.5)), int(hr) + 2)
            pygame.draw.circle(s, head, (c, int(c - hr * 0.5)), int(hr))
            if weapon_color:
                pygame.draw.line(s, weapon_color, (c + bw / 2, c + bh * 0.3), (c + bw / 2 + size * 0.28, c - size * 0.1), max(2, size // 12))

        def mech(color):
            pygame.draw.rect(s, _darken(color, 0.4), (c - r, c - r * 0.7, r * 2, r * 1.4), border_radius=4)
            pygame.draw.rect(s, color, (c - r * 0.8, c - r * 0.5, r * 1.6, r), border_radius=4)
            pygame.draw.rect(s, _darken(color, 0.7), (c - r, c + r * 0.35, r * 2, r * 0.4))
            pygame.draw.rect(s, _darken(color, 0.7), (c - r, c - r * 0.75, r * 2, r * 0.4))
            pygame.draw.circle(s, _lighten(color, 0.4), (c, c), max(2, size // 8))
            pygame.draw.line(s, _lighten(color, 0.3), (c, c), (c + r * 1.05, c), max(2, size // 10))

        def glow_orb(color):
            for i in range(4, 0, -1):
                a = 40 + (4 - i) * 45
                col = (*_lighten(color, (4 - i) * 0.2), min(255, a))
                pygame.draw.circle(s, col, (c, c), int(r * i / 4))
            pygame.draw.circle(s, (255, 255, 255), (c, c), max(2, int(r * 0.25)))

        k = key
        # --- player forms per era ---
        if k == "player_0":
            blob((90, 230, 170), 0.18)
            pygame.draw.circle(s, (30, 120, 90), (int(c + r * 0.15), int(c - r * 0.1)), max(2, size // 6))
            eyes(dx=0.32, dy=-0.28)
        elif k == "player_1":
            blob((220, 150, 60), 0.15, cx=c, cy=c + size * 0.05, rad=r * 0.95)
            for sx in (-1, 1):  # legs
                for lx in (0.35, 0.7):
                    pygame.draw.line(s, (140, 90, 40), (c + sx * r * lx, c + r * 0.5), (c + sx * r * (lx + 0.15), c + r * 0.95), max(2, size // 14))
            eyes(dx=0.3, dy=-0.25)
            spikes = [(c - r * 0.2 + i * r * 0.25, c - r * 0.8 - (i % 2) * r * 0.15) for i in range(3)]
            for px, py in spikes:
                pygame.draw.polygon(s, (160, 100, 40), [(px - 4, c - r * 0.4), (px + 4, c - r * 0.4), (px, py)])
        elif k == "player_2":
            humanoid((150, 100, 60), (230, 180, 140), weapon_color=(200, 160, 100))
            pygame.draw.rect(s, (200, 60, 40), (c - size * 0.22, c + size * 0.02, size * 0.44, size * 0.08))  # war paint sash
        elif k == "player_3":
            humanoid((90, 100, 120), (220, 190, 160), weapon_color=(120, 130, 150))
            pygame.draw.rect(s, (140, 150, 170), (c - size * 0.24, c - size * 0.02, size * 0.48, size * 0.14), border_radius=2)  # chest plate
        elif k == "player_4":
            humanoid((210, 215, 235), (120, 230, 255), weapon_color=(80, 240, 255))
            pygame.draw.circle(s, (255, 255, 255), (c, int(c - size * 0.1)), int(size * 0.16), 2)  # helmet visor
        # --- cell era enemies ---
        elif k == "amoeba":
            blob((120, 200, 120), 0.3)
            pygame.draw.circle(s, (60, 120, 60), (c, c), max(2, size // 7))
        elif k == "bacteria":
            blob((90, 170, 200), 0.25, points=8)
        elif k == "virus":
            spiky((200, 90, 160), spikes=9, inner_f=0.55)
            pygame.draw.circle(s, (120, 40, 100), (c, c), max(2, size // 6))
        # --- creature era ---
        elif k == "insect":
            blob((170, 140, 60), 0.2, points=8)
            eyes((255, 60, 60), dx=0.4, dy=-0.2, er=max(2, size // 12))
            for sx in (-1, 1):
                for i in range(3):
                    pygame.draw.line(s, (110, 90, 40), (c, c), (c + sx * r * 1.1, c - r * 0.5 + i * r * 0.5), max(1, size // 18))
        elif k == "raptor":
            pygame.draw.polygon(s, (60, 140, 70), [(c - r, c + r * 0.6), (c + r, c), (c - r * 0.4, c - r * 0.7)])
            pygame.draw.polygon(s, (90, 190, 100), [(c - r * 0.8, c + r * 0.45), (c + r * 0.8, c), (c - r * 0.35, c - r * 0.5)])
            eyes((255, 220, 80), dx=0.25, dy=-0.15, er=max(2, size // 12))
        elif k == "beast":
            blob((150, 90, 50), 0.18)
            eyes((255, 80, 60), dx=0.35, dy=-0.2)
            for sx in (-1, 1):  # tusks
                pygame.draw.polygon(s, (240, 230, 200), [(c + sx * r * 0.5, c + r * 0.3), (c + sx * r * 0.7, c + r * 0.3), (c + sx * r * 0.6, c + r * 0.8)])
        # --- tribe era ---
        elif k == "wolf":
            pygame.draw.polygon(s, (110, 110, 120), [(c - r, c + r * 0.5), (c + r, c), (c - r * 0.3, c - r * 0.6)])
            pygame.draw.polygon(s, (150, 150, 160), [(c - r * 0.8, c + r * 0.35), (c + r * 0.8, c), (c - r * 0.25, c - r * 0.45)])
            eyes((255, 200, 60), dx=0.2, dy=-0.1, er=max(2, size // 12))
        elif k == "hunter":
            humanoid((140, 90, 50), (220, 170, 130), weapon_color=(230, 200, 150))
        elif k == "brute":
            humanoid((100, 70, 40), (200, 150, 110))
            pygame.draw.rect(s, (80, 60, 40), (c - size * 0.3, c - size * 0.05, size * 0.6, size * 0.1))
        # --- civilization era ---
        elif k == "drone":
            pygame.draw.rect(s, (100, 110, 130), (c - r * 0.5, c - r * 0.5, r, r), border_radius=3)
            for sx in (-1, 1):
                for sy in (-1, 1):
                    pygame.draw.circle(s, (60, 70, 90), (int(c + sx * r * 0.8), int(c + sy * r * 0.8)), max(2, size // 8), 2)
            pygame.draw.circle(s, (255, 80, 80), (c, c), max(2, size // 9))
        elif k == "soldier":
            humanoid((70, 90, 70), (200, 170, 140), weapon_color=(50, 50, 60))
        elif k == "armor_unit":
            mech((120, 130, 150))
        # --- space era ---
        elif k == "energy_being":
            glow_orb((120, 220, 255))
        elif k == "alien":
            humanoid((100, 60, 150), (160, 255, 160), weapon_color=(80, 240, 255))
        elif k == "robot":
            mech((90, 100, 200))
        # --- bosses ---
        elif k == "boss_amoeba":
            blob((100, 220, 140), 0.28, points=16)
            pygame.draw.circle(s, (40, 130, 80), (c, c), int(r * 0.35))
            for i in range(5):
                a = i / 5 * math.tau
                pygame.draw.circle(s, (60, 160, 100), (int(c + math.cos(a) * r * 0.55), int(c + math.sin(a) * r * 0.55)), max(2, size // 14))
            eyes(dx=0.2, dy=-0.3, er=max(3, size // 12))
        elif k == "boss_predator":
            pygame.draw.polygon(s, (140, 60, 40), [(c - r, c + r * 0.7), (c + r, c), (c - r * 0.5, c - r * 0.8)])
            pygame.draw.polygon(s, (190, 90, 60), [(c - r * 0.8, c + r * 0.5), (c + r * 0.85, c), (c - r * 0.4, c - r * 0.6)])
            eyes((255, 240, 100), dx=0.25, dy=-0.15, er=max(3, size // 12))
            for i in range(4):  # teeth
                x = c + r * 0.3 + i * r * 0.14
                pygame.draw.polygon(s, (255, 245, 220), [(x, c + r * 0.1), (x + r * 0.07, c + r * 0.1), (x + r * 0.035, c + r * 0.3)])
        elif k == "boss_shaman":
            humanoid((120, 60, 40), (210, 160, 120), weapon_color=(255, 160, 60))
            pygame.draw.circle(s, (255, 170, 60), (int(c + size * 0.34), int(c - size * 0.16)), max(3, size // 9))
            for i in range(4):  # headdress
                a = math.pi * (0.25 + 0.166 * i)
                pygame.draw.line(s, (240, 200, 90), (c, c - size * 0.18), (c + math.cos(a) * size * 0.32, c - size * 0.18 - math.sin(a) * size * 0.3), max(2, size // 16))
        elif k == "boss_tank":
            mech((150, 70, 70))
            pygame.draw.line(s, (220, 120, 110), (c, c), (c + r * 1.1, c - r * 0.4), max(3, size // 9))
        elif k == "boss_god":
            glow_orb((190, 120, 255))
            for i in range(6):
                a = i / 6 * math.tau
                x2, y2 = c + math.cos(a) * r, c + math.sin(a) * r
                pygame.draw.line(s, (240, 200, 255, 180), (c, c), (x2, y2), max(2, size // 16))
            pygame.draw.circle(s, (255, 255, 255), (c, c), int(r * 0.3))
            pygame.draw.circle(s, (60, 20, 120), (c, c), int(r * 0.16))
        else:
            blob((200, 200, 200), 0.2)
        return s

    # ------------------------------------------------------------------
    # UI icons: real art from /assets/icons/<key>.svg (game-icons.net,
    # CC-BY 3.0 - see CREDITS.md), recolored to the requested color.
    # Falls back to procedural shapes for unknown keys.
    # ------------------------------------------------------------------
    def icon(self, key, color, size=36, fallback=None):
        ck = ("icon", key, tuple(color), size)
        if ck in self._cache:
            return self._cache[ck]
        surf = self._icon_file(key, tuple(color), size)
        if surf is None and fallback:
            surf = self._icon_file(fallback, tuple(color), size)
        if surf is None:
            surf = self._gen_icon(fallback or key, color, size)
        self._cache[ck] = surf
        return surf

    def _icon_file(self, key, color, size):
        base_ck = ("icon_base", key)
        base = self._cache.get(base_ck)
        if base is None:
            base = False
            for ext in (".svg", ".png"):
                path = os.path.join(ASSET_DIR, "icons", key + ext)
                if os.path.exists(path):
                    try:
                        base = pygame.image.load(path).convert_alpha()
                        break
                    except pygame.error:
                        pass
            self._cache[base_ck] = base
        if base is False:
            return None
        # game-icons render as a white glyph on an opaque black square:
        # use luminance as alpha and flat-fill with the requested color.
        sm = pygame.transform.smoothscale(base, (size, size))
        out = pygame.Surface((size, size), pygame.SRCALPHA)
        r, g, b = color[:3]
        for y in range(size):
            for x in range(size):
                lum = sm.get_at((x, y)).r
                if lum:
                    out.set_at((x, y), (r, g, b, lum))
        return out

    def _gen_icon(self, kind, color, size=36):
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        r = size * 0.38
        col = tuple(color)
        dark = _darken(col, 0.5)
        if kind == "nearest":
            pygame.draw.polygon(s, col, [(c - r, c + r * 0.6), (c + r, c), (c - r, c - r * 0.6)])
            pygame.draw.polygon(s, dark, [(c - r, c + r * 0.6), (c + r, c), (c - r, c - r * 0.6)], 2)
        elif kind == "aura":
            for rr, a in ((r, 90), (r * 0.66, 150), (r * 0.33, 230)):
                pygame.draw.circle(s, (*col, a), (c, c), int(rr))
        elif kind == "orbit":
            pygame.draw.circle(s, dark, (c, c), int(r), 2)
            pygame.draw.circle(s, col, (c + int(r), c), max(2, size // 8))
            pygame.draw.circle(s, col, (c - int(r), c), max(2, size // 8))
        elif kind in ("nova", "spread"):
            for i in range(8 if kind == "nova" else 3):
                a = i / 8 * math.tau if kind == "nova" else -0.5 + i * 0.5
                pygame.draw.line(s, col, (c, c), (c + math.cos(a) * r, c + math.sin(a) * r), max(2, size // 10))
        elif kind == "chain":
            pts = [(c - r, c - r * 0.7), (c, c - r * 0.1), (c - r * 0.3, c + r * 0.1), (c + r, c + r * 0.8)]
            pygame.draw.lines(s, col, False, pts, max(2, size // 9))
        elif kind == "accessory":
            pygame.draw.polygon(s, col, [(c, c - r), (c + r, c), (c, c + r), (c - r, c)])
            pygame.draw.polygon(s, dark, [(c, c - r), (c + r, c), (c, c + r), (c - r, c)], 2)
        elif kind == "stat":
            pygame.draw.polygon(s, col, [(c, c - r), (c + r * 0.8, c + r * 0.3), (c + r * 0.35, c + r * 0.3), (c + r * 0.35, c + r), (c - r * 0.35, c + r), (c - r * 0.35, c + r * 0.3), (c - r * 0.8, c + r * 0.3)])
        elif kind == "heal":
            pygame.draw.rect(s, col, (c - r * 0.3, c - r, r * 0.6, r * 2))
            pygame.draw.rect(s, col, (c - r, c - r * 0.3, r * 2, r * 0.6))
        elif kind == "evo":
            # double helix hint
            for i in range(7):
                t = i / 6
                y = c - r + t * 2 * r
                x_off = math.sin(t * math.pi * 2) * r * 0.6
                pygame.draw.circle(s, col, (int(c + x_off), int(y)), max(2, size // 12))
                pygame.draw.circle(s, dark, (int(c - x_off), int(y)), max(2, size // 12))
        elif kind == "energy":
            pygame.draw.polygon(s, col, [(c + r * 0.2, c - r), (c - r * 0.5, c + r * 0.15), (c, c + r * 0.15), (c - r * 0.2, c + r), (c + r * 0.5, c - r * 0.15), (c, c - r * 0.15)])
        elif kind == "lock":
            pygame.draw.rect(s, col, (c - r * 0.6, c - r * 0.1, r * 1.2, r), border_radius=3)
            pygame.draw.circle(s, col, (c, int(c - r * 0.3)), int(r * 0.45), max(2, size // 12))
        else:
            pygame.draw.circle(s, col, (c, c), int(r))
        return s
