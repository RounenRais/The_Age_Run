"""In-run HUD: HP / XP / energy / timer / era banner / build slots / boss bar."""
import math

import pygame

from ui.theme import draw_bar, draw_panel, text

W, H = 1280, 720


def fmt_time(t):
    return "%02d:%02d" % (t // 60, t % 60)


def draw_hud(surf, run):
    game = run.game
    fonts = game.fonts
    theme = run.theme
    p = run.player
    pulse = 1 + 0.03 * math.sin(pygame.time.get_ticks() * 0.004)  # cell-membrane heartbeat

    # --- top-left: HP -------------------------------------------------
    hp_w = int(250 * pulse) if run.era == 0 else 250
    draw_bar(surf, (18, 16, hp_w, 26), p.hp / p.max_hp, (225, 60, 70), theme, segments=10)
    text(surf, fonts["small"], "%d/%d" % (p.hp, p.max_hp), (255, 255, 255), (26, 22))
    if p.revives > 0:
        icon = game.assets.icon("revive", (255, 220, 120), 18)
        surf.blit(icon, (18, 48))
        text(surf, fonts["tiny"], "x%d" % p.revives, (255, 220, 120), (40, 52))

    # --- top-center: XP bar + level badge -------------------------------
    xp_rect = pygame.Rect(330, 14, 620, 18)
    draw_bar(surf, xp_rect, p.xp / p.xp_needed, theme.accent, theme)
    badge = fonts["small"].render("LV %d" % p.level, False, theme.dark)
    br = badge.get_rect(center=(xp_rect.centerx, xp_rect.centery + 1)).inflate(14, 8)
    pygame.draw.rect(surf, theme.accent, br)
    pygame.draw.rect(surf, theme.dark, br, 2)
    surf.blit(badge, badge.get_rect(center=br.center))

    # --- top-right: energy + timer --------------------------------------
    icon = game.assets.icon("energy", (255, 220, 90), 22)
    surf.blit(icon, (W - 236, 14))
    text(surf, fonts["body"], "%d" % run.energy, (255, 220, 90), (W - 208, 17))
    text(surf, fonts["body"], fmt_time(run.time), (255, 255, 255), (W - 18, 17), anchor="topright")
    evo_icon = game.assets.icon("evo", (230, 130, 255), 18)
    surf.blit(evo_icon, (W - 110, 44))
    text(surf, fonts["small"], "+%d" % run.evo_earned, (230, 130, 255), (W - 18, 46), anchor="topright")

    # --- bottom-right: era banner + wave indicator ----------------------
    era_data = game.data["eras"][run.era]
    label = fonts["small"].render(era_data["name"], False, theme.accent)
    wave = fonts["body"].render(run.spawner.wave_label, False, theme.text)
    bw = max(label.get_width(), wave.get_width()) + 66
    panel = pygame.Rect(W - bw - 14, H - 70, bw, 56)
    draw_panel(surf, panel, theme, border=3)
    era_icon = game.assets.icon(era_data["icon"], theme.accent, 34)
    surf.blit(era_icon, era_icon.get_rect(midleft=(panel.left + 8, panel.centery)))
    surf.blit(label, label.get_rect(midtop=(panel.centerx + 20, panel.top + 8)))
    surf.blit(wave, wave.get_rect(midtop=(panel.centerx + 20, panel.top + 28)))

    # --- bottom-left: build slots ----------------------------------------
    x = 16
    y = H - 50
    for w in p.weapons:
        icon = game.assets.icon(w.id, w.data.get("color", (255, 255, 255)), 30,
                                fallback=w.data["behavior"])
        r = pygame.Rect(x, y, 38, 38)
        pygame.draw.rect(surf, theme.dark, r)
        pygame.draw.rect(surf, theme.primary, r, 2)
        surf.blit(icon, icon.get_rect(center=r.center))
        for i in range(w.level):  # level pips
            pygame.draw.rect(surf, theme.accent, (x + 3 + i * 4, y + 33, 3, 3))
        x += 44
    for _ in range(p.weapon_slots - len(p.weapons)):
        r = pygame.Rect(x, y, 38, 38)
        pygame.draw.rect(surf, theme.dark, r)
        pygame.draw.rect(surf, (70, 70, 80), r, 2)
        x += 44
    x += 10
    for aid, lvl in p.accessories.items():
        d = p.acc_data[aid]
        icon = game.assets.icon(d["stat"], theme.accent, 24, fallback="accessory")
        r = pygame.Rect(x, y + 5, 30, 30)
        pygame.draw.rect(surf, theme.dark, r)
        pygame.draw.rect(surf, (120, 120, 140), r, 2)
        surf.blit(icon, icon.get_rect(center=r.center))
        for i in range(lvl):
            pygame.draw.rect(surf, theme.accent, (x + 2 + i * 4, y + 33, 3, 3))
        x += 36

    # --- boss bar ---------------------------------------------------------
    boss = run.boss
    if boss and not boss.dead:
        bar = pygame.Rect(W // 2 - 320, 58, 640, 22)
        text(surf, fonts["body"], boss.data["name"], (255, 130, 130),
             (bar.centerx, bar.top - 6), anchor="midbottom", outline=True)
        segments = 3 if boss.eid == "godlike_entity" else 1
        draw_bar(surf, bar, boss.hp / boss.max_hp, (235, 70, 90), theme, segments=segments)

    # --- FPS -----------------------------------------------------------
    if game.show_fps:
        text(surf, fonts["tiny"], "FPS %d" % int(game.clock.get_fps()), (160, 160, 160),
             (W - 18, 72), anchor="topright")
