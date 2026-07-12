"""EVOLUTION SURVIVORS - a Spore-themed roguelite survivor (pygame).

Controls: WASD/arrows move, weapons auto-fire, ESC pause,
F11 fullscreen, F3 FPS counter, F2 CRT overlay.
"""
import sys

import pygame

from systems import gamedata
from systems.asset_loader import AssetLoader
from systems.audio import Audio
from systems.meta_progression import MetaProgression
from systems.save_system import SaveSystem

W, H = 1280, 720
FPS = 60


class Game:
    def __init__(self):
        self.audio = Audio()  # pre-inits mixer before display init
        pygame.init()
        pygame.display.set_caption("EVOLUTION SURVIVORS")
        self.screen = pygame.display.set_mode((W, H), pygame.SCALED)
        self.clock = pygame.time.Clock()
        self.running = True
        self.show_fps = True
        self.crt_on = True

        self.data = gamedata.load_all()
        self.save = SaveSystem()
        self.meta = MetaProgression(self.save, self.data["upgrades"])
        self.assets = AssetLoader()

        from ui.theme import load_fonts, make_crt_overlay
        self.fonts = load_fonts()
        self.crt = make_crt_overlay((W, H))

        from states.build_select import BuildSelectState
        from states.game_over import GameOverState
        from states.hub import HubState
        from states.main_menu import MainMenuState
        from states.pause import PauseState
        from states.run_state import RunState
        from states.victory import VictoryState
        self.states = {
            "main_menu": MainMenuState(self),
            "hub": HubState(self),
            "run": RunState(self),
            "build_select": BuildSelectState(self),
            "pause": PauseState(self),
            "game_over": GameOverState(self),
            "victory": VictoryState(self),
        }
        self.state = self.states["main_menu"]
        self.state.enter()

    def change_state(self, name, **kwargs):
        self.state.exit()
        self.state = self.states[name]
        self.state.enter(**kwargs)

    def quit(self):
        self.running = False

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
                    self.show_fps = not self.show_fps
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
                    self.crt_on = not self.crt_on
                else:
                    self.state.handle_event(event)
            self.state.update(dt)
            self.state.draw(self.screen)
            if self.crt_on:
                self.crt.set_alpha(230 if pygame.time.get_ticks() % 900 < 40 else 255)
                self.screen.blit(self.crt, (0, 0))
            if self.show_fps and self.state is not self.states.get("run"):
                fps = self.fonts["tiny"].render("FPS %d" % int(self.clock.get_fps()), False, (140, 140, 140))
                self.screen.blit(fps, (W - 70, H - 18))
            pygame.display.flip()
        self.save.save()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
    sys.exit(0)
