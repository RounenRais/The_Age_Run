import math
import random

import pygame

from states.state import State
from ui.theme import LAB_THEME
from ui.widgets import Button

W, H = 1280, 720


class MainMenuState(State):
    def enter(self, **kwargs):
        cx = W // 2
        self.buttons = [
            Button((cx - 170, 340, 340, 56), "START RUN"),
            Button((cx - 170, 416, 340, 56), "LABORATORY"),
            Button((cx - 170, 492, 340, 56), "QUIT"),
        ]
        self.t = 0.0
        self.sel = 0
        self._bg = self._make_bg()

    def _make_bg(self):
        bg = pygame.Surface((W, H))
        eras = self.game.data["eras"]
        band_w = W // len(eras)
        rng = random.Random(7)
        for i, era in enumerate(eras):
            base = era["bg_color"]
            rect = pygame.Rect(i * band_w, 0, band_w + 1, H)
            bg.fill(base, rect)
            accent = era["palette"]["primary"]
            for _ in range(26):
                c = tuple(min(255, (b + a) // 2) for b, a in zip(base, accent))
                pygame.draw.circle(bg, c, (rng.randint(rect.left, rect.right), rng.randint(0, H)),
                                   rng.randint(1, 4))
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 130))
        bg.blit(dim, (0, 0))
        return bg

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - 1) % len(self.buttons)
                self.game.audio.play("blip")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + 1) % len(self.buttons)
                self.game.audio.play("blip")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate(self.sel)
        for i, b in enumerate(self.buttons):
            if b.clicked(event):
                self._activate(i)

    def _activate(self, i):
        self.game.audio.play("confirm")
        if i == 0:
            self.game.change_state("run", new_run=True)
        elif i == 1:
            self.game.change_state("hub")
        else:
            self.game.quit()

    def update(self, dt):
        self.t += dt
        mp = pygame.mouse.get_pos()
        for i, b in enumerate(self.buttons):
            b.update_hover(mp, self.game.audio)
            if b.hover:
                self.sel = i
            b.hover = b.hover or (i == self.sel)

    def draw(self, surf):
        # slow panning collage of the five era backgrounds
        off = int((math.sin(self.t * 0.1) * 0.5 + 0.5) * 0)
        surf.blit(self._bg, (off, 0))
        fonts = self.game.fonts
        glow = 1 + 0.15 * math.sin(self.t * 3)
        title = fonts["title"].render("EVOLUTION", False, (140, 255, 220))
        title2 = fonts["title"].render("SURVIVORS", False, (255, 220, 120))
        for img, y in ((title, 130), (title2, 190)):
            sh = img.copy()
            sh.set_alpha(int(70 * glow))
            surf.blit(sh, sh.get_rect(center=(W // 2 + 3, y + 3)))
            surf.blit(img, img.get_rect(center=(W // 2, y)))
        from ui.theme import text
        text(surf, fonts["small"], "FROM CELL TO GODHOOD - DIE, EVOLVE, REPEAT",
             (200, 220, 220), (W // 2, 248), anchor="center")
        for b in self.buttons:
            b.draw(surf, LAB_THEME, fonts)
        evo_icon = self.game.assets.icon("evo", (230, 130, 255), 22)
        surf.blit(evo_icon, evo_icon.get_rect(midright=(W // 2 - 96, 590)))
        text(surf, fonts["small"], "EVO POINTS: %d" % self.game.save.evo,
             (230, 130, 255), (W // 2 + 12, 590), anchor="center")
        text(surf, fonts["small"], "WASD MOVE - WEAPONS AUTO-FIRE - F11 FULLSCREEN",
             (170, 180, 180), (W // 2, 680), anchor="center")
