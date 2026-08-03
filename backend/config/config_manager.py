import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "default_config.json"


class ConfigManager:
    def __init__(self):
        self.config = {}

    def load(self):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def get(self, *keys, default=None):
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default

    def save(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)