import os
import json

HOME = os.environ.get("HOME")
CONFIG_FOLDER = f"{HOME}/.config/kiwi-shell"
CONFIG_FILE = f"{CONFIG_FOLDER}/config.json"
HYPR_FILE = f"{CONFIG_FOLDER}/hypr.conf"
BORDER_OPACITY = 0.7

os.makedirs(CONFIG_FOLDER, exist_ok=True)

_config = {}

def _load():
    global _config
    try:
        with open(CONFIG_FILE) as f:
            _config = json.load(f)
    except Exception:
        _config = {}

_load()

def get(key, default=None):
    return _config.get(key, default)

def set(key, value):
    _config[key] = value

def _hex_to_rgba(hex_color: str):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    return r, g, b

def _rgba_to_hypr(r, g, b, a) -> str:
    return "rgba({:02x}{:02x}{:02x}{:02x})".format(
        int(r * 255), int(g * 255), int(b * 255), int(a * 255)
    )

def write_conf():
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(_config, f, indent=2)
    except Exception as e:
        print(f"Failed to save config: {e}")

    try:
        primary = _config.get("primary_color", "#ffffff")
        r, g, b = _hex_to_rgba(primary)
        kiwi_color = _rgba_to_hypr(r, g, b, 1.0)
        kiwi_color_transparent = _rgba_to_hypr(r, g, b, BORDER_OPACITY)
        hypr = f"$kiwiColor = {kiwi_color}\n$kiwiColorLight = {kiwi_color_transparent}\n"
        with open(HYPR_FILE, "w") as f:
            f.write(hypr)
    except Exception as e:
        print(f"Failed to save hypr colors: {e}")