"""Persistent save data: meta currency, permanent upgrades, unlocks, stats."""
import json
import os

SAVE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "save.json")

DEFAULT = {
    "evolution_points": 0,
    "upgrades": {},          # upgrade_id -> level
    "unlocked": [],          # weapon ids bought in the hub
    "stats": {
        "total_runs": 0,
        "best_era": 0,       # 1-based era reached; 6 = game cleared
        "total_kills": 0,
        "playtime": 0.0,     # seconds spent in runs
        "victories": 0,
    },
}


class SaveSystem:
    def __init__(self):
        self.data = json.loads(json.dumps(DEFAULT))
        self.load()

    def load(self):
        if os.path.exists(SAVE_PATH):
            try:
                with open(SAVE_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                for k, v in loaded.items():
                    if k == "stats":
                        self.data["stats"].update(v)
                    else:
                        self.data[k] = v
            except (json.JSONDecodeError, OSError):
                pass  # corrupt save: keep defaults, will be rewritten on save

    def save(self):
        try:
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except OSError:
            pass

    # -- convenience accessors -------------------------------------------
    @property
    def evo(self):
        return self.data["evolution_points"]

    @evo.setter
    def evo(self, value):
        self.data["evolution_points"] = max(0, int(value))

    def upgrade_level(self, upgrade_id):
        return self.data["upgrades"].get(upgrade_id, 0)

    def is_unlocked(self, weapon_id):
        return weapon_id in self.data["unlocked"]

    def record_run(self, era_reached, kills, run_time, victory):
        s = self.data["stats"]
        s["total_runs"] += 1
        s["best_era"] = max(s["best_era"], 6 if victory else era_reached)
        s["total_kills"] += kills
        s["playtime"] += run_time
        if victory:
            s["victories"] += 1
        self.save()
