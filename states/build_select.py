"""Era transition: drag & drop build management.

Drag a new option card onto a weapon slot to add/replace it (or onto the
passive row for accessories), drag existing weapon slots onto each other to
reorder, plus a small Energy shop. Click + CONFIRM still works when there is
a free slot.
"""
import random

import pygame

from states.state import State
from systems.weapons import Weapon
from ui import theme as thm
from ui.theme import draw_panel, text
from ui.widgets import Button, Card

W, H = 1280, 720
SLOT = 52          # weapon slot size
ACC_SLOT = 44      # passive slot size


class BuildSelectState(State):
    def enter(self, run=None, **kwargs):
        self.run = run
        g = self.game
        self.old_era = run.era
        self.new_era = run.era + 1
        self.old_theme = thm.era_theme(g.data["eras"], self.old_era)
        self.theme = thm.era_theme(g.data["eras"], self.new_era)
        self.wipe_t = 1.2          # era-morph screen wipe
        self.picked = None         # selected option card (click flow)
        self.applied = False       # a new pick has been placed
        self.drag = None           # {"type": "new"/"slot", ...}
        self.warn_t = 0.0
        self.warn_text = ""
        g.audio.play("era")

        self._make_option_cards()
        self.confirm_btn = Button((W // 2 + 40, H - 66, 280, 48), "CONFIRM")
        self.skip_btn = Button((W // 2 - 320, H - 66, 280, 48), "SKIP PICK")
        self._make_shop()

    # ------------------------------------------------------------------
    def _make_option_cards(self):
        g, run = self.game, self.run
        pool = []
        owned_weapons = {w.id for w in run.player.weapons}
        for wd in g.data["weapons"]:
            if wd["era"] != self.new_era or wd["id"] in owned_weapons:
                continue
            if wd.get("locked") and not g.save.is_unlocked(wd["id"]):
                continue
            pool.append(("weapon", wd))
        for ad in g.data["accessories"]:
            if ad["era"] == self.new_era and run.player.accessories.get(ad["id"], 0) < 5:
                pool.append(("accessory", ad))
        random.shuffle(pool)
        pool = pool[:4]

        self.cards = []
        n = max(1, len(pool))
        cw, ch, gap = 252, 250, 22
        x0 = W // 2 - (n * cw + (n - 1) * gap) // 2
        for i, (kind, data) in enumerate(pool):
            rect = pygame.Rect(x0 + i * (cw + gap), 168, cw, ch)
            if kind == "weapon":
                icon = g.assets.icon(data["id"], data["color"], 48, fallback=data["behavior"])
                lines = ["NEW WEAPON", data["desc"]]
                accent = tuple(data["color"])
            else:
                icon = g.assets.icon(data["stat"], self.theme.accent, 48, fallback="accessory")
                lines = ["NEW PASSIVE", data["desc"]]
                accent = None
            card = Card(rect, data["name"], lines, icon=icon, accent=accent)
            card.kind = (kind, data)
            card.drag_icon = icon
            self.cards.append(card)

    def _make_shop(self):
        mult = self.new_era + 1
        self.shop = [
            {"name": "FULL REPAIR", "desc": "HEAL ALL", "cost": 40 * mult, "effect": "heal"},
            {"name": "OVERCHARGE", "desc": "+10% DMG", "cost": 60 * mult, "effect": "damage"},
            {"name": "ADRENALINE", "desc": "+8% SPEED", "cost": 45 * mult, "effect": "speed"},
        ]
        self.shop_btns = []
        x0 = W // 2 - 396
        for i, offer in enumerate(self.shop):
            b = Button((x0 + i * 272, H - 158, 250, 42), offer["name"], "small")
            self.shop_btns.append(b)

    # ------------------------------------------------------------------
    def _weapon_slot_rects(self):
        p = self.run.player
        x0 = W // 2 - 330
        return [pygame.Rect(x0 + i * (SLOT + 8), 468, SLOT, SLOT)
                for i in range(p.weapon_slots)]

    def _acc_slot_rects(self):
        p = self.run.player
        x0 = W // 2 + 60
        return [pygame.Rect(x0 + i * (ACC_SLOT + 6), 472, ACC_SLOT, ACC_SLOT)
                for i in range(p.acc_slots)]

    def _warn(self, msg):
        self.warn_text = msg
        self.warn_t = 2.0
        self.game.audio.play("deny")

    # ------------------------------------------------------------------
    # dragging
    # ------------------------------------------------------------------
    def _start_drag(self, event):
        if event.button != 1:
            return
        if not self.applied:
            for c in self.cards:
                if c.rect.collidepoint(event.pos):
                    self.picked = c
                    for o in self.cards:
                        o.selected = o is c
                    kind, data = c.kind
                    self.drag = {"type": "new", "card": c, "kind": kind, "data": data,
                                 "icon": c.drag_icon}
                    self.game.audio.play("blip")
                    return
        weapons = self.run.player.weapons
        for i, r in enumerate(self._weapon_slot_rects()):
            if r.collidepoint(event.pos) and i < len(weapons):
                w = weapons[i]
                icon = self.game.assets.icon(w.id, w.data["color"], 48,
                                             fallback=w.data["behavior"])
                self.drag = {"type": "slot", "idx": i, "icon": icon}
                self.game.audio.play("blip")
                return

    def _end_drag(self, event):
        drag, self.drag = self.drag, None
        if drag is None or event.button != 1:
            return
        p = self.run.player
        slot_rects = self._weapon_slot_rects()
        target = None
        for i, r in enumerate(slot_rects):
            if r.collidepoint(event.pos):
                target = i
                break

        if drag["type"] == "slot":
            src = drag["idx"]
            if target is not None and target != src:
                if target < len(p.weapons):
                    p.weapons[src], p.weapons[target] = p.weapons[target], p.weapons[src]
                else:
                    p.weapons.append(p.weapons.pop(src))
                self.game.audio.play("confirm")
            return

        # dragging a new option card
        kind, data = drag["kind"], drag["data"]
        if kind == "weapon":
            if target is None:
                return  # dropped nowhere: keep it selected, no action
            if target < len(p.weapons):
                p.weapons[target] = Weapon(data)
            else:
                p.weapons.append(Weapon(data))
            self._mark_applied()
        else:
            over_acc = any(r.collidepoint(event.pos) for r in self._acc_slot_rects())
            if over_acc or target is not None:
                p.add_accessory(data)
                self._mark_applied()

    def _mark_applied(self):
        self.applied = True
        self.picked = None
        for c in self.cards:
            c.enabled = False
            c.selected = False
        self.confirm_btn.text = "CONTINUE"
        self.skip_btn.enabled = False
        self.game.audio.play("confirm")

    # ------------------------------------------------------------------
    def handle_event(self, event):
        g, run = self.game, self.run
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._start_drag(event)
        elif event.type == pygame.MOUSEBUTTONUP:
            self._end_drag(event)

        for b, offer in zip(self.shop_btns, self.shop):
            if b.clicked(event):
                if offer.get("bought"):
                    continue
                if run.energy >= offer["cost"]:
                    run.energy -= offer["cost"]
                    self._apply_shop(offer)
                    offer["bought"] = True
                    g.audio.play("buy")
                else:
                    g.audio.play("deny")
        if self.confirm_btn.clicked(event) or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
            self._confirm()
        if self.skip_btn.enabled and self.skip_btn.clicked(event):
            g.audio.play("confirm")
            g.change_state("run", advance_era=True)

    def _apply_shop(self, offer):
        p = self.run.player
        if offer["effect"] == "heal":
            p.heal(p.max_hp)
        elif offer["effect"] == "damage":
            p.run_damage_bonus += 0.10
            p.recalc()
        elif offer["effect"] == "speed":
            p.run_speed_bonus += 0.08
            p.recalc()

    def _confirm(self):
        g, run = self.game, self.run
        if self.applied:
            g.change_state("run", advance_era=True)
            return
        if self.picked is None:
            self._warn("PICK A CARD FIRST (OR SKIP)")
            return
        kind, data = self.picked.kind
        p = run.player
        if kind == "weapon":
            if len(p.weapons) < p.weapon_slots:
                p.weapons.append(Weapon(data))
            else:
                self._warn("SLOTS FULL - DRAG THE CARD ONTO A WEAPON TO REPLACE IT")
                return
        else:
            p.add_accessory(data)
        g.audio.play("confirm")
        g.change_state("run", advance_era=True)

    # ------------------------------------------------------------------
    def update(self, dt):
        self.wipe_t = max(0.0, self.wipe_t - dt)
        self.warn_t = max(0.0, self.warn_t - dt)
        mp = pygame.mouse.get_pos()
        for c in self.cards:
            c.update_hover(mp, self.game.audio)
        self.confirm_btn.update_hover(mp, self.game.audio)
        self.skip_btn.update_hover(mp, self.game.audio)
        for b in self.shop_btns:
            b.update_hover(mp, self.game.audio)

    # ------------------------------------------------------------------
    def draw(self, surf):
        g, run = self.game, self.run
        fonts = g.fonts
        eras = g.data["eras"]
        theme = self.theme
        surf.fill(eras[self.new_era]["bg_color"])
        if self.wipe_t > 0:  # old era palette wipes away to the right
            wipe_w = int(W * (self.wipe_t / 1.2))
            pygame.draw.rect(surf, eras[self.old_era]["bg_color"], (W - wipe_w, 0, wipe_w, H))

        text(surf, fonts["med"], "%s COMPLETE!" % eras[self.old_era]["name"],
             self.old_theme.accent, (W // 2, 38), anchor="center")
        text(surf, fonts["big"], "ENTERING %s" % eras[self.new_era]["name"],
             theme.accent, (W // 2, 86), anchor="center", outline=True)
        hint = ("DRAG A CARD ONTO YOUR BUILD - DRAG WEAPONS ONTO EACH OTHER TO REORDER"
                if not self.applied else "PICK APPLIED - PRESS CONTINUE")
        text(surf, fonts["small"], hint, theme.text, (W // 2, 130), anchor="center")

        for c in self.cards:
            c.draw(surf, theme, fonts)

        # ---- build rows -------------------------------------------------
        mp = pygame.mouse.get_pos()
        p = run.player
        dragging_weapon = self.drag and (self.drag["type"] == "slot"
                                         or self.drag.get("kind") == "weapon")
        dragging_acc = self.drag and self.drag.get("kind") == "accessory"

        text(surf, fonts["small"], "WEAPONS", theme.accent, (W // 2 - 330, 448))
        for i, r in enumerate(self._weapon_slot_rects()):
            pygame.draw.rect(surf, theme.dark, r)
            hot = r.collidepoint(mp)
            if i < len(p.weapons):
                w = p.weapons[i]
                w_theme = thm.era_theme(eras, w.data["era"])
                border = theme.accent if (dragging_weapon and hot) else w_theme.primary
                pygame.draw.rect(surf, border, r, 4 if (dragging_weapon and hot) else 3)
                icon = g.assets.icon(w.id, w.data["color"], 38, fallback=w.data["behavior"])
                surf.blit(icon, icon.get_rect(center=r.center))
                text(surf, fonts["tiny"], str(w.level), theme.text,
                     (r.right - 4, r.bottom - 4), anchor="bottomright")
            else:
                border = theme.accent if (dragging_weapon and hot) else (85, 85, 95)
                pygame.draw.rect(surf, border, r, 4 if (dragging_weapon and hot) else 2)

        text(surf, fonts["small"], "PASSIVES", theme.accent, (W // 2 + 60, 448))
        acc_items = list(p.accessories.items())
        for i, r in enumerate(self._acc_slot_rects()):
            pygame.draw.rect(surf, theme.dark, r)
            hot = r.collidepoint(mp)
            if i < len(acc_items):
                aid, lvl = acc_items[i]
                d = p.acc_data[aid]
                pygame.draw.rect(surf, (140, 140, 160), r, 2)
                icon = g.assets.icon(d["stat"], theme.accent, 30, fallback="accessory")
                surf.blit(icon, icon.get_rect(center=r.center))
                text(surf, fonts["tiny"], str(lvl), theme.text,
                     (r.right - 4, r.bottom - 4), anchor="bottomright")
            else:
                border = theme.accent if (dragging_acc and hot) else (85, 85, 95)
                pygame.draw.rect(surf, border, r, 4 if (dragging_acc and hot) else 2)

        # ---- energy shop --------------------------------------------------
        shop_panel = pygame.Rect(W // 2 - 420, H - 172, 840, 88)
        draw_panel(surf, shop_panel, theme, 3)
        en_icon = g.assets.icon("energy", (255, 220, 90), 20)
        surf.blit(en_icon, (shop_panel.left + 4, shop_panel.top - 28))
        text(surf, fonts["small"], "ENERGY: %d" % run.energy, (255, 220, 90),
             (shop_panel.left + 30, shop_panel.top - 24))
        for b, offer in zip(self.shop_btns, self.shop):
            b.enabled = not offer.get("bought")
            b.text = offer["name"] if not offer.get("bought") else "SOLD"
            b.draw(surf, theme, fonts)
            text(surf, fonts["tiny"], "%s - %d ENERGY" % (offer["desc"], offer["cost"]),
                 theme.text, (b.rect.centerx, b.rect.bottom + 6), anchor="midtop")

        self.confirm_btn.draw(surf, theme, fonts)
        if self.skip_btn.enabled:
            self.skip_btn.draw(surf, theme, fonts)

        if self.warn_t > 0:
            text(surf, fonts["small"], self.warn_text, (255, 160, 120),
                 (W // 2, 152), anchor="center", outline=True)

        # ---- drag ghost ----------------------------------------------------
        if self.drag:
            icon = self.drag["icon"]
            ghost = pygame.transform.smoothscale(icon, (56, 56))
            pygame.draw.circle(surf, theme.accent, mp, 34, 2)
            surf.blit(ghost, ghost.get_rect(center=mp))
