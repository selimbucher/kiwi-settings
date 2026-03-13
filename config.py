import json
import os

CONFIG_PATH = os.path.expanduser("~/.config/kiwi-shell/config.json")

def load_config() -> dict:
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_config(config: dict):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def get(key: str, default=None):
    return load_config().get(key, default)

def set(key: str, value):
    config = load_config()
    config[key] = value
    save_config(config)