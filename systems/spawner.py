"""Wave-based enemy spawner for one era."""
import random

from pygame.math import Vector2

ARENA_W, ARENA_H = 1280, 720
MAX_ENEMIES = 220


def edge_position():
    side = random.randint(0, 3)
    if side == 0:
        return Vector2(random.uniform(0, ARENA_W), -30)
    if side == 1:
        return Vector2(random.uniform(0, ARENA_W), ARENA_H + 30)
    if side == 2:
        return Vector2(-30, random.uniform(0, ARENA_H))
    return Vector2(ARENA_W + 30, random.uniform(0, ARENA_H))


class Spawner:
    def __init__(self, era_data, era_index):
        self.era = era_data
        self.era_index = era_index
        self.waves = era_data["waves"]
        self.wave_index = 0
        self.wave_timer = self.waves[0]["duration"]
        self.spawn_timer = 1.0
        self.boss_active = False
        self.boss_spawned = False
        self.elite_spawned = False
        self.done = False   # boss killed -> era over (run state flips this)

    @property
    def total_waves(self):
        return len(self.waves) + 1  # + boss wave

    @property
    def wave_label(self):
        if self.boss_active:
            return "BOSS"
        return "WAVE %d/%d" % (self.wave_index + 1, self.total_waves)

    def hp_scale(self):
        # waves get tougher as the era progresses
        return 1.0 + 0.12 * self.wave_index

    def update(self, dt, run):
        if self.done:
            return
        if self.boss_active:
            if not self.boss_spawned:
                self.boss_spawned = True
                run.spawn_boss(self.era["boss"])
            # light trickle of adds during the boss fight
            self.spawn_timer -= dt
            if self.spawn_timer <= 0 and len(run.enemies) < 25:
                self.spawn_timer = 4.5
                self._spawn_from_wave(run, self.waves[-1])
            return

        wave = self.waves[self.wave_index]
        self.wave_timer -= dt
        self.spawn_timer -= dt

        if self.spawn_timer <= 0 and len(run.enemies) < MAX_ENEMIES:
            self.spawn_timer = wave["interval"]
            self._spawn_from_wave(run, wave)

        # one elite mid-wave from wave 2 onwards
        if (not self.elite_spawned and self.wave_index >= 1
                and self.wave_timer < wave["duration"] * 0.5):
            self.elite_spawned = True
            eid = self._pick(wave)
            run.spawn_enemy(eid, elite=True, hp_scale=self.hp_scale())

        if self.wave_timer <= 0:
            run.on_wave_complete(self.wave_index)
            self.wave_index += 1
            self.elite_spawned = False
            if self.wave_index >= len(self.waves):
                self.boss_active = True
                self.spawn_timer = 6.0
            else:
                self.wave_timer = self.waves[self.wave_index]["duration"]

    def _pick(self, wave):
        ids = list(wave["enemies"].keys())
        weights = list(wave["enemies"].values())
        return random.choices(ids, weights=weights)[0]

    def _spawn_from_wave(self, run, wave):
        run.spawn_enemy(self._pick(wave), hp_scale=self.hp_scale())
