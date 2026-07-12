import pygame

from states.state import State
from ui.theme import LAB_THEME, draw_panel
from ui.widgets import Button

W, H = 1280, 720


def fmt_time(t):
    return "%02d:%02d" % (t // 60, t % 60)


class GameOverState(State):
    TITLE = "YOU DIED"
    TITLE_COLOR = (235, 70, 70)
    SOUND = "gameover"

    def enter(self, stats=None, bg=None, **kwargs):
        self.stats = stats or {}
        self.bg = bg
        self.t = 0.0
        cx = W // 2
        self.retry_btn = Button((cx - 340, 520, 320, 54), "RETRY")
        self.hub_btn = Button((cx + 20, 520, 320, 54), "BACK TO HUB")
        self.game.audio.play(self.SOUND)

    def handle_event(self, event):
        if self.retry_btn.clicked(event) or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
            self.game.audio.play("confirm")
            self.game.change_state("run", new_run=True)
        if self.hub_btn.clicked(event) or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            self.game.change_state("hub")

    def update(self, dt):
        self.t += dt
        mp = pygame.mouse.get_pos()
        self.retry_btn.update_hover(mp, self.game.audio)
        self.hub_btn.update_hover(mp, self.game.audio)

    def draw(self, surf):
        if self.bg:
            surf.blit(self.bg, (0, 0))
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 190))
        surf.blit(dim, (0, 0))
        fonts = self.game.fonts
        s = self.stats
        title = fonts["huge"].render(self.TITLE, False, self.TITLE_COLOR)
        surf.blit(title, title.get_rect(center=(W // 2, 150)))

        panel = pygame.Rect(W // 2 - 260, 220, 520, 250)
        draw_panel(surf, panel, LAB_THEME, 4)
        era_names = [e["name"] for e in self.game.data["eras"]]
        era_label = era_names[min(s.get("era", 0), len(era_names) - 1)]
        # evolution points count up over ~1.2 seconds
        evo_shown = int(min(1.0, self.t / 1.2) * s.get("evo", 0))
        lines = [
            ("ERA REACHED", era_label),
            ("RUN TIME", fmt_time(s.get("time", 0))),
            ("ENEMIES KILLED", str(s.get("kills", 0))),
            ("LEVEL", str(s.get("level", 1))),
            ("EVO POINTS EARNED", "+%d" % evo_shown),
        ]
        for i, (k, v) in enumerate(lines):
            y = panel.top + 26 + i * 42
            ki = fonts["small"].render(k, False, (170, 190, 190))
            vi = fonts["body"].render(v, False, (230, 130, 255) if "EVO" in k else (240, 240, 240))
            surf.blit(ki, (panel.left + 24, y))
            surf.blit(vi, vi.get_rect(topright=(panel.right - 24, y - 2)))
        self.retry_btn.draw(surf, LAB_THEME, fonts)
        self.hub_btn.draw(surf, LAB_THEME, fonts)
