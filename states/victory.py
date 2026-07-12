import math

import pygame

from states.game_over import GameOverState

W, H = 1280, 720


class VictoryState(GameOverState):
    TITLE = "EVOLUTION COMPLETE!"
    TITLE_COLOR = (140, 255, 200)
    SOUND = "victory"

    def draw(self, surf):
        super().draw(surf)
        fonts = self.game.fonts
        glow = 0.5 + 0.5 * math.sin(self.t * 4)
        banner = fonts["med"].render("FROM A SINGLE CELL TO GODHOOD", False,
                                     (int(150 + 100 * glow), 220, 255))
        surf.blit(banner, banner.get_rect(center=(W // 2, 200)))
