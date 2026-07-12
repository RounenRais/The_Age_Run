"""Synthesized arcade-style sound effects (no audio files needed).

Real sound files can later replace these by loading from /assets/sfx; the
`play(name)` interface stays the same.
"""
import math
import random
import struct

import pygame

SAMPLE_RATE = 22050


def _pack(samples):
    return struct.pack("<%dh" % len(samples), *samples)


def _tone(freq, dur, vol=0.4, shape="square", decay=True, slide=0.0):
    n = int(SAMPLE_RATE * dur)
    out = []
    phase = 0.0
    for i in range(n):
        t = i / n
        f = freq + slide * t * freq
        phase += f / SAMPLE_RATE
        p = phase % 1.0
        if shape == "square":
            v = 1.0 if p < 0.5 else -1.0
        elif shape == "saw":
            v = 2.0 * p - 1.0
        elif shape == "noise":
            v = random.uniform(-1, 1)
        else:  # sine
            v = math.sin(p * math.tau)
        env = (1.0 - t) if decay else 1.0
        out.append(int(v * env * vol * 32767))
    return out


def _seq(*parts):
    samples = []
    for p in parts:
        samples.extend(p)
    return samples


class Audio:
    def __init__(self):
        self.enabled = True
        try:
            pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)
            pygame.mixer.init(SAMPLE_RATE, -16, 1, 512)
            pygame.mixer.set_num_channels(24)
        except pygame.error:
            self.enabled = False
            return
        self.sounds = {}
        self._build()

    def _build(self):
        S = self.sounds
        S["blip"] = _tone(880, 0.05, 0.18)
        S["confirm"] = _seq(_tone(660, 0.06, 0.25), _tone(990, 0.09, 0.25))
        S["deny"] = _seq(_tone(220, 0.08, 0.25), _tone(160, 0.12, 0.25))
        S["shoot"] = _tone(520, 0.05, 0.10, "saw", slide=-0.5)
        S["hit"] = _tone(200, 0.06, 0.16, "noise")
        S["hurt"] = _seq(_tone(180, 0.1, 0.35, "saw"), _tone(120, 0.12, 0.3, "saw"))
        S["pickup"] = _tone(1040, 0.06, 0.14, "sine", slide=0.6)
        S["energy"] = _tone(1560, 0.05, 0.10, "sine")
        S["levelup"] = _seq(_tone(523, 0.07, 0.3), _tone(659, 0.07, 0.3), _tone(784, 0.07, 0.3), _tone(1047, 0.16, 0.3))
        S["explosion"] = _tone(90, 0.35, 0.4, "noise")
        S["boss_roar"] = _seq(_tone(80, 0.3, 0.45, "saw", decay=False, slide=0.4), _tone(110, 0.35, 0.45, "saw"))
        S["boss_die"] = _seq(_tone(300, 0.15, 0.4, "noise"), _tone(150, 0.3, 0.45, "noise"), _tone(70, 0.5, 0.5, "noise"))
        S["era"] = _seq(_tone(392, 0.1, 0.3), _tone(523, 0.1, 0.3), _tone(659, 0.1, 0.3), _tone(784, 0.1, 0.3), _tone(1047, 0.3, 0.35))
        S["buy"] = _seq(_tone(784, 0.06, 0.25), _tone(1175, 0.12, 0.25))
        S["gameover"] = _seq(_tone(392, 0.2, 0.35), _tone(311, 0.2, 0.35), _tone(233, 0.4, 0.4))
        S["victory"] = _seq(_tone(523, 0.12, 0.3), _tone(659, 0.12, 0.3), _tone(784, 0.12, 0.3), _tone(1047, 0.12, 0.35), _tone(784, 0.1, 0.3), _tone(1047, 0.5, 0.4))
        for k, samples in S.items():
            S[k] = pygame.mixer.Sound(buffer=_pack(samples))

    def play(self, name):
        if not self.enabled:
            return
        snd = self.sounds.get(name)
        if snd:
            snd.play()
