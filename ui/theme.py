"""Era-reactive arcade UI theme: palettes, fonts, panels, bars, CRT overlay."""
import os
import random

import pygame

FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "assets", "fonts", "PressStart2P.ttf")


class Theme:
    """Palette wrapper; one per era plus a default 'lab' theme for menus."""

    def __init__(self, palette):
        self.primary = tuple(palette["primary"])
        self.accent = tuple(palette["accent"])
        self.dark = tuple(palette["dark"])
        self.panel = tuple(palette["panel"])
        self.text = tuple(palette["text"])


LAB_THEME = Theme({
    "primary": [80, 200, 190],
    "accent": [140, 255, 240],
    "dark": [12, 30, 34],
    "panel": [18, 42, 48],
    "text": [220, 250, 250],
})


def load_fonts():
    sizes = {"tiny": 10, "small": 12, "body": 15, "med": 19, "big": 26, "huge": 36, "title": 48}
    fonts = {}
    for name, size in sizes.items():
        try:
            fonts[name] = pygame.font.Font(FONT_PATH, size)
        except (OSError, pygame.error):
            fonts[name] = pygame.font.SysFont("couriernew", size + 6, bold=True)
    return fonts


def text(surf, font, string, color, pos, anchor="topleft", shadow=True, outline=False):
    """Render text with a drop shadow (or full outline) for readability on
    busy backgrounds. Returns the text rect."""
    img = font.render(string, False, color)
    rect = img.get_rect(**{anchor: pos})
    if outline:
        dark = font.render(string, False, (10, 10, 14))
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            surf.blit(dark, rect.move(dx, dy))
    elif shadow:
        dark = font.render(string, False, (10, 10, 14))
        surf.blit(dark, rect.move(2, 2))
    surf.blit(img, rect)
    return rect


def era_theme(eras_data, era_index):
    return Theme(eras_data[max(0, min(era_index, len(eras_data) - 1))]["palette"])


def draw_panel(surf, rect, theme, border=4):
    """Chunky arcade panel: thick border + accent corner ticks."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(surf, theme.dark, rect.inflate(border * 2, border * 2))
    pygame.draw.rect(surf, theme.primary, rect.inflate(border * 2, border * 2), border)
    pygame.draw.rect(surf, theme.panel, rect)
    t = border + 2
    for cx, cy, dx, dy in ((rect.left, rect.top, 1, 1), (rect.right, rect.top, -1, 1),
                           (rect.left, rect.bottom, 1, -1), (rect.right, rect.bottom, -1, -1)):
        pygame.draw.line(surf, theme.accent, (cx, cy), (cx + dx * t * 3, cy), 3)
        pygame.draw.line(surf, theme.accent, (cx, cy), (cx, cy + dy * t * 3), 3)


def draw_bar(surf, rect, frac, color, theme, segments=0, back=(16, 14, 18)):
    rect = pygame.Rect(rect)
    frac = max(0.0, min(1.0, frac))
    pygame.draw.rect(surf, theme.dark, rect.inflate(6, 6))
    pygame.draw.rect(surf, back, rect)
    if frac > 0:
        fill = rect.copy()
        fill.width = max(1, int(rect.width * frac))
        pygame.draw.rect(surf, color, fill)
        hi = fill.copy()
        hi.height = max(1, rect.height // 4)
        light = tuple(min(255, c + 70) for c in color)
        pygame.draw.rect(surf, light, hi)
    if segments > 1:
        step = rect.width / segments
        for i in range(1, segments):
            x = int(rect.left + i * step)
            pygame.draw.line(surf, theme.dark, (x, rect.top), (x, rect.bottom - 1), 2)
    pygame.draw.rect(surf, theme.primary, rect.inflate(6, 6), 2)


def make_crt_overlay(size):
    """Scanline + vignette overlay blitted over the final frame."""
    w, h = size
    ov = pygame.Surface(size, pygame.SRCALPHA)
    for y in range(0, h, 3):
        pygame.draw.line(ov, (0, 0, 0, 28), (0, y), (w, y))
    edge = pygame.Surface(size, pygame.SRCALPHA)
    for i, a in ((0, 90), (6, 50), (14, 25)):
        pygame.draw.rect(edge, (0, 0, 0, a), pygame.Rect(i, i, w - 2 * i, h - 2 * i), 8)
    ov.blit(edge, (0, 0))
    return ov


def flicker_alpha():
    return random.randint(0, 100) < 4
