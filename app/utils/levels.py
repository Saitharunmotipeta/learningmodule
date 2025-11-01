import json
import os

LEVELS_PATH = "app/data/levels.json"

def load_levels():
    if not os.path.exists(LEVELS_PATH):
        return {}
    with open(LEVELS_PATH, "r") as f:
        return json.load(f)

def get_words_for_level(level: str):
    data = load_levels()
    return data.get(level, [])
