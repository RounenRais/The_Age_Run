"""Applies permanent hub upgrades to run stats and handles purchases."""


class MetaProgression:
    def __init__(self, save, upgrades_data):
        self.save = save
        self.upgrades = {u["id"]: u for u in upgrades_data}

    def bonus(self, stat):
        """Total bonus for a stat across all owned upgrade levels."""
        total = 0
        for uid, up in self.upgrades.items():
            if up["stat"] == stat:
                total += up["per_level"] * self.save.upgrade_level(uid)
        return total

    def cost(self, upgrade_id):
        up = self.upgrades[upgrade_id]
        lvl = self.save.upgrade_level(upgrade_id)
        if lvl >= up["max_level"]:
            return None
        return int(round(up["base_cost"] * (up["cost_growth"] ** lvl)))

    def can_buy(self, upgrade_id):
        c = self.cost(upgrade_id)
        return c is not None and self.save.evo >= c

    def buy(self, upgrade_id):
        c = self.cost(upgrade_id)
        if c is None or self.save.evo < c:
            return False
        self.save.evo -= c
        ups = self.save.data["upgrades"]
        ups[upgrade_id] = ups.get(upgrade_id, 0) + 1
        self.save.save()
        return True

    def unlock_weapon(self, weapon):
        cost = weapon.get("cost", 0)
        if self.save.is_unlocked(weapon["id"]) or self.save.evo < cost:
            return False
        self.save.evo -= cost
        self.save.data["unlocked"].append(weapon["id"])
        self.save.save()
        return True
