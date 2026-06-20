import json
import os

from core.service import Service

SAVE_FILE = "savegame.json"
STATS_FILE = "stats.json"


class SaveService(Service):
    def __init__(self):
        self.total_coins = 0

    def init(self):
        self._load_stats()

    def _load_stats(self):
        self.total_coins = 0
        try:
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE) as f:
                    data = json.load(f)
                    self.total_coins = data.get("total_coins", 0)
        except Exception:
            pass

    def save_stats(self, total_coins):
        try:
            with open(STATS_FILE, "w") as f:
                json.dump({"total_coins": total_coins}, f)
        except Exception as e:
            print(f"Error saving stats: {e}")

    def has_save_file(self):
        if not os.path.exists(SAVE_FILE):
            return False
        try:
            with open(SAVE_FILE, "r") as f:
                save_data = json.load(f)
            return save_data.get("save_valid", False)
        except Exception:
            return False

    def load_game(self):
        if not os.path.exists(SAVE_FILE):
            return None
        try:
            with open(SAVE_FILE, "r") as f:
                save_data = json.load(f)
            if not save_data.get("save_valid", False):
                return None
            return save_data
        except Exception:
            return None

    def save_game(self, data):
        data["save_valid"] = True
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving game: {e}")

    def invalidate_save(self):
        try:
            if os.path.exists(SAVE_FILE):
                with open(SAVE_FILE, "r") as f:
                    save_data = json.load(f)
                save_data["save_valid"] = False
                with open(SAVE_FILE, "w") as f:
                    json.dump(save_data, f)
        except Exception as e:
            print(f"Error invalidating save: {e}")

    def clear_save(self):
        if os.path.exists(SAVE_FILE):
            try:
                os.remove(SAVE_FILE)
            except Exception as e:
                print(f"Error removing save: {e}")
