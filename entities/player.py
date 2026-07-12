import pygame
from pygame.math import Vector2

ARENA = pygame.Rect(0, 0, 1280, 720)


class Player:
    def __init__(self, game, run):
        self.game = game
        self.run = run
        meta = game.meta
        self.pos = Vector2(ARENA.width / 2, ARENA.height / 2)
        self.radius = 16

        # base stats (meta upgrades applied here, accessories via recalc)
        self.base_max_hp = 80 + meta.bonus("max_hp")
        self.base_speed = 210 * (1 + meta.bonus("speed_pct"))
        self.base_damage_mult = 1 + meta.bonus("damage_pct")
        self.base_regen = meta.bonus("regen")
        self.base_armor = meta.bonus("armor")
        self.base_xp_mult = 1 + meta.bonus("xp_pct")
        self.energy_mult = 1 + meta.bonus("energy_pct")
        self.evo_mult = 1 + meta.bonus("evo_pct")
        self.weapon_slots = min(6, 4 + int(meta.bonus("weapon_slots")))
        self.acc_slots = 6
        self.revives = int(meta.bonus("revive"))

        # in-run temporary boosts (era-transition mini shop)
        self.run_damage_bonus = 0.0
        self.run_speed_bonus = 0.0

        self.weapons = []        # Weapon instances
        self.accessories = {}    # acc_id -> level
        self.acc_data = {}       # acc_id -> data dict

        self.level = 1
        self.xp = 0.0
        self.hp = self.base_max_hp
        self.iframes = 0.0
        self.facing = 1
        self.recalc()
        self.hp = self.max_hp

    # ------------------------------------------------------------------
    def _acc_total(self, stat):
        return sum(d["amount"] * self.accessories[aid]
                   for aid, d in self.acc_data.items() if d["stat"] == stat)

    def recalc(self):
        old_max = getattr(self, "max_hp", None)
        self.max_hp = self.base_max_hp + self._acc_total("max_hp")
        if old_max is None:
            self.hp = self.max_hp
        else:
            self.hp = min(self.max_hp, self.hp + max(0, self.max_hp - old_max))
        self.speed = self.base_speed * (1 + self._acc_total("speed_pct") + self.run_speed_bonus)
        self.damage_mult = self.base_damage_mult * (1 + self._acc_total("damage_pct") + self.run_damage_bonus)
        self.cooldown_mult = 1.0 / (1.0 + self._acc_total("cooldown_pct"))
        self.regen = self.base_regen + self._acc_total("regen")
        self.armor = self.base_armor + self._acc_total("armor")
        self.crit = 0.05 + self._acc_total("crit")
        self.xp_mult = self.base_xp_mult * (1 + self._acc_total("xp_pct"))
        self.pickup_radius = 90 * (1 + self._acc_total("pickup_pct"))

    @property
    def xp_needed(self):
        return 10 + (self.level - 1) * 8

    # ------------------------------------------------------------------
    def update(self, dt):
        keys = pygame.key.get_pressed()
        move = Vector2(
            (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT]),
            (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP]))
        if move.length_squared() > 0:
            move = move.normalize()
            if move.x:
                self.facing = 1 if move.x > 0 else -1
        self.pos += move * self.speed * dt
        self.pos.x = max(self.radius, min(ARENA.width - self.radius, self.pos.x))
        self.pos.y = max(self.radius, min(ARENA.height - self.radius, self.pos.y))

        self.iframes = max(0.0, self.iframes - dt)
        if self.regen > 0 and self.hp < self.max_hp:
            self.hp = min(self.max_hp, self.hp + self.regen * dt)

        for w in self.weapons:
            w.update(dt, self.run, self)

    # ------------------------------------------------------------------
    def take_damage(self, dmg, ignore_iframes=False):
        if self.iframes > 0 and not ignore_iframes:
            return
        dmg = max(1, dmg - self.armor)
        self.hp -= dmg
        self.iframes = max(self.iframes, 0.5)
        self.run.on_player_hit(dmg)
        if self.hp <= 0:
            if self.revives > 0:
                self.revives -= 1
                self.hp = self.max_hp * 0.5
                self.iframes = 2.5
                self.run.on_player_revive()
            else:
                self.hp = 0
                self.run.on_player_death()

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def gain_xp(self, value):
        self.xp += value * self.xp_mult
        levels = 0
        while self.xp >= self.xp_needed:
            self.xp -= self.xp_needed
            self.level += 1
            levels += 1
        if levels:
            self.run.queue_levelups(levels)

    # ------------------------------------------------------------------
    def add_accessory(self, data):
        aid = data["id"]
        self.acc_data[aid] = data
        self.accessories[aid] = self.accessories.get(aid, 0) + 1
        self.recalc()

    def draw(self, surf, assets, era):
        size = int(self.radius * 2.6)
        spr = assets.sprite("player_%d" % era, size)
        if self.facing < 0:
            spr = pygame.transform.flip(spr, True, False)
        rect = spr.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        if self.iframes > 0 and int(self.iframes * 14) % 2 == 0:
            ghost = spr.copy()
            ghost.set_alpha(110)
            surf.blit(ghost, rect)
        else:
            surf.blit(spr, rect)
