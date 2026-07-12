import pygame

from states.state import State
from ui.theme import LAB_THEME
from ui.widgets import Button

W, H = 1280, 720


class PauseState(State):
    def enter(self, bg=None, **kwargs):
        self.bg = bg
        cx = W // 2
        self.resume_btn = Button((cx - 160, 330, 320, 54), "RESUME")
        self.quit_btn = Button((cx - 160, 404, 320, 54), "QUIT TO HUB")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.game.change_state("run", resume=True)
        if self.resume_btn.clicked(event):
            self.game.change_state("run", resume=True)
        if self.quit_btn.clicked(event):
            # abandoning a run still banks the evolution points earned so far
            run = self.game.states["run"]
            self.game.save.evo += run.evo_earned
            self.game.save.record_run(run.era + 1, run.kills, run.time, False)
            self.game.change_state("hub")

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        self.resume_btn.update_hover(mp, self.game.audio)
        self.quit_btn.update_hover(mp, self.game.audio)

    def draw(self, surf):
        if self.bg:
            surf.blit(self.bg, (0, 0))
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 170))
        surf.blit(dim, (0, 0))
        fonts = self.game.fonts
        run = self.game.states["run"]
        theme = getattr(run, "theme", LAB_THEME)
        title = fonts["huge"].render("PAUSED", False, theme.accent)
        surf.blit(title, title.get_rect(center=(W // 2, 220)))
        # current build reference on the side
        y = 300
        for w in run.player.weapons:
            icon = self.game.assets.icon(w.id, w.data["color"], 26,
                                         fallback=w.data["behavior"])
            surf.blit(icon, (40, y))
            txt = fonts["tiny"].render("%s LV%d" % (w.data["name"], w.level), False, theme.text)
            surf.blit(txt, (74, y + 8))
            y += 34
        for aid, lvl in run.player.accessories.items():
            txt = fonts["tiny"].render("%s LV%d" % (run.player.acc_data[aid]["name"], lvl),
                                       False, (170, 180, 190))
            surf.blit(txt, (40, y + 6))
            y += 26
        self.resume_btn.draw(surf, theme, fonts)
        self.quit_btn.draw(surf, theme, fonts)
