"""Loads all JSON game data from /data."""
import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _load(name):
    with open(os.path.join(DATA_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


def load_all():
    return {
        "eras": _load("eras.json"),
        "enemies": _load("enemies.json"),
        "weapons": _load("weapons.json"),
        "accessories": _load("accessories.json"),
        "upgrades": _load("upgrades.json"),
    }
