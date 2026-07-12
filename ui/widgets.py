"""Arcade UI widgets: buttons and selection cards."""
import pygame

from ui.theme import draw_panel


class Button:
    def __init__(self, rect, text, font_key="med"):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font_key = font_key
        self.hover = False
        self.enabled = True
        self._was_hover = False

    def update_hover(self, mouse_pos, audio=None):
        self.hover = self.enabled and self.rect.collidepoint(mouse_pos)
        if self.hover and not self._was_hover and audio:
            audio.play("blip")
        self._was_hover = self.hover

    def clicked(self, event):
        return (self.enabled and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1 and self.rect.collidepoint(event.pos))

    def draw(self, surf, theme, fonts):
        r = self.rect.inflate(6, 6) if self.hover else self.rect
        color = theme.accent if self.hover else theme.primary
        pygame.draw.rect(surf, theme.dark, r)
        pygame.draw.rect(surf, color, r, 4)
        font = fonts[self.font_key]
        txt_color = theme.text if self.enabled else (110, 110, 110)
        img = font.render(self.text, False, txt_color)
        shadow = font.render(self.text, False, (10, 10, 14))
        surf.blit(shadow, shadow.get_rect(center=(r.centerx + 2, r.centery + 2)))
        surf.blit(img, img.get_rect(center=r.center))
        if self.hover:
            pygame.draw.rect(surf, color, r.inflate(8, 8), 1)


class Card:
    """Selection card used by level-up, build select and hub screens."""

    def __init__(self, rect, title, lines, icon=None, accent=None, footer=None):
        self.rect = pygame.Rect(rect)
        self.title = title
        self.lines = lines          # list of short description strings
        self.icon = icon            # Surface or None
        self.accent = accent        # override border color
        self.footer = footer        # bottom line (e.g. cost / hotkey)
        self.hover = False
        self.selected = False
        self.enabled = True
        self._was_hover = False

    def update_hover(self, mouse_pos, audio=None):
        self.hover = self.enabled and self.rect.collidepoint(mouse_pos)
        if self.hover and not self._was_hover and audio:
            audio.play("blip")
        self._was_hover = self.hover

    def clicked(self, event):
        return (self.enabled and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1 and self.rect.collidepoint(event.pos))

    def draw(self, surf, theme, fonts):
        r = self.rect.inflate(8, 8) if (self.hover or self.selected) else self.rect
        accent = self.accent or theme.primary
        border = theme.accent if (self.hover or self.selected) else accent
        pygame.draw.rect(surf, theme.dark, r.inflate(8, 8))
        pygame.draw.rect(surf, border, r.inflate(8, 8), 4)
        pygame.draw.rect(surf, theme.panel, r)
        if not self.enabled:
            dim = pygame.Surface(r.size, pygame.SRCALPHA)
            dim.fill((0, 0, 0, 120))
        y = r.top + 14
        if self.icon:
            # dark plate behind the icon so bright icons stay crisp
            plate = self.icon.get_rect(midtop=(r.centerx, y)).inflate(16, 12)
            pygame.draw.rect(surf, theme.dark, plate, border_radius=4)
            surf.blit(self.icon, self.icon.get_rect(midtop=(r.centerx, y)))
            y += self.icon.get_height() + 12
        title_font = fonts["body"]
        title_color = theme.accent if self.enabled else (120, 120, 120)
        for tline in _wrap(self.title, title_font, r.width - 16):
            img = title_font.render(tline, False, title_color)
            sh = title_font.render(tline, False, (10, 10, 14))
            rect = img.get_rect(midtop=(r.centerx, y))
            surf.blit(sh, rect.move(2, 2))
            surf.blit(img, rect)
            y += img.get_height() + 5
        y += 8
        body_font = fonts["small"]
        for line in self.lines:
            for sub in _wrap(line, body_font, r.width - 20):
                img = body_font.render(sub, False, theme.text if self.enabled else (120, 120, 120))
                surf.blit(img, img.get_rect(midtop=(r.centerx, y)))
                y += img.get_height() + 5
        if self.footer:
            img = fonts["small"].render(self.footer, False, border)
            surf.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom - 8)))
        if not self.enabled:
            surf.blit(dim, r.topleft)
        if self.selected:
            pygame.draw.rect(surf, theme.accent, r.inflate(16, 16), 2)


def _wrap(text, font, width):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if font.size(trial)[0] <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines
