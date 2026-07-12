"""Laboratory / evolution chamber: spend Evolution Points on permanent upgrades."""
import pygame

from states.state import State
from ui.theme import LAB_THEME, draw_panel
from ui.widgets import Button, Card

W, H = 1280, 720


class HubState(State):
    def enter(self, **kwargs):
        self.game.save.save()
        self.theme = LAB_THEME
        self.start_btn = Button((W - 320, H - 80, 300, 56), "START RUN")
        self.back_btn = Button((20, H - 80, 200, 56), "MAIN MENU")
        self._build_cards()

    def _build_cards(self):
        g = self.game
        self.cards = []
        upgrades = g.data["upgrades"]
        cw, ch, gap = 232, 148, 12
        x0, y0 = 20, 96
        per_row = 5
        for i, up in enumerate(upgrades):
            r = pygame.Rect(x0 + (i % per_row) * (cw + gap), y0 + (i // per_row) * (ch + gap + 8), cw, ch)
            lvl = g.save.upgrade_level(up["id"])
            cost = g.meta.cost(up["id"])
            footer = "MAXED" if cost is None else "COST %d EVO" % cost
            card = Card(r, up["name"], [up["desc"], "LEVEL %d/%d" % (lvl, up["max_level"])],
                        icon=g.assets.icon(up["stat"], self.theme.accent, 34, fallback="stat"),
                        footer=footer)
            card.kind = ("upgrade", up)
            card.enabled = cost is not None
            if cost is not None and g.save.evo < cost:
                card.accent = (110, 110, 120)
            self.cards.append(card)
        # weapon unlocks row
        y2 = y0 + 2 * (ch + gap + 8) + 30
        locked = [wd for wd in g.data["weapons"] if wd.get("locked")]
        for i, wd in enumerate(locked):
            r = pygame.Rect(x0 + i * (cw + gap), y2, cw, ch)
            owned = g.save.is_unlocked(wd["id"])
            footer = "UNLOCKED" if owned else "UNLOCK %d EVO" % wd["cost"]
            icon_key = wd["id"] if owned else "lock"
            card = Card(r, wd["name"], [wd["desc"], "ERA %d WEAPON" % (wd["era"] + 1)],
                        icon=g.assets.icon(icon_key, wd["color"], 34, fallback=wd["behavior"]),
                        accent=tuple(wd["color"]) if owned else (120, 120, 130), footer=footer)
            card.kind = ("unlock", wd)
            card.enabled = not owned
            self.cards.append(card)
        self._unlock_row_y = y2

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.change_state("main_menu")
            return
        if self.start_btn.clicked(event):
            self.game.audio.play("confirm")
            self.game.change_state("run", new_run=True)
            return
        if self.back_btn.clicked(event):
            self.game.change_state("main_menu")
            return
        for c in self.cards:
            if c.clicked(event):
                kind, data = c.kind
                ok = (self.game.meta.buy(data["id"]) if kind == "upgrade"
                      else self.game.meta.unlock_weapon(data))
                self.game.audio.play("buy" if ok else "deny")
                if ok:
                    self._build_cards()
                break

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        self.start_btn.update_hover(mp, self.game.audio)
        self.back_btn.update_hover(mp, self.game.audio)
        for c in self.cards:
            c.update_hover(mp, self.game.audio)

    def draw(self, surf):
        g = self.game
        fonts = g.fonts
        surf.fill((10, 22, 26))
        title = fonts["big"].render("EVOLUTION LABORATORY", False, self.theme.accent)
        surf.blit(title, (20, 22))
        evo_icon = g.assets.icon("evo", (230, 130, 255), 26)
        surf.blit(evo_icon, (W - 330, 20))
        evo = fonts["med"].render("%d EVO POINTS" % g.save.evo, False, (230, 130, 255))
        surf.blit(evo, (W - 296, 24))

        lbl = fonts["small"].render("PERMANENT MUTATIONS", False, (150, 190, 190))
        surf.blit(lbl, (20, 76))
        lbl2 = fonts["small"].render("WEAPON UNLOCKS", False, (150, 190, 190))
        surf.blit(lbl2, (20, self._unlock_row_y - 20))
        for c in self.cards:
            c.draw(surf, self.theme, fonts)

        # stats panel
        s = g.save.data["stats"]
        panel = pygame.Rect(W - 480, H - 200, 450, 100)
        draw_panel(surf, panel, self.theme, 3)
        lines = [
            "RUNS %d   VICTORIES %d" % (s["total_runs"], s["victories"]),
            "BEST ERA %s   KILLS %d" % (("%d" % s["best_era"]) if s["best_era"] else "-", s["total_kills"]),
            "PLAYTIME %dm" % (s["playtime"] // 60),
        ]
        for i, line in enumerate(lines):
            img = fonts["small"].render(line, False, self.theme.text)
            surf.blit(img, (panel.left + 16, panel.top + 14 + i * 24))

        self.start_btn.draw(surf, self.theme, fonts)
        self.back_btn.draw(surf, self.theme, fonts)
