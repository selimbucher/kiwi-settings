import json
import os
import re

HOME = os.path.expanduser("~")
CONFIG_FOLDER = os.path.join(HOME, ".config", "kiwi-shell")
CONFIG_FILE = os.path.join(CONFIG_FOLDER, "config.json")
HYPR_FILE = os.path.join(CONFIG_FOLDER, "hypr.conf")
BORDER_OPACITY = 0.7

# kiwi-shell's defaultConfig.json: what the shell uses for a missing key
DEFAULTS = {
    "primary_color": "rgb(190,157,241)",
    "bar_margin": 4,
    "dock_margin": 4,
    "theme": "acrylic",
    "kiwi_blur": True,
    "dock": "auto-hide",
    "dock_home": True,
    "dock_trash": True,
    "auto_color": True,
    "dock_icon_size": 46,
    "dock_full_width": False,
    "desktop_icons": True,
    "desktop_free_placement": True,
    "popup_monitor": "active",
    "dock_arpeggio": False,
    "indicator_bar_position": "bottom",
    "auto_nightshift": False,
    "nightshift_start": "20:30",
    "nightshift_end": "06:00",
    "nightshift_intensity": 4000,
    "shortcuts": {
        "launcher": "Super",
        "app_switcher": "Alt+Tab",
        "workspace_switcher": "Super+Tab",
    },
}

os.makedirs(CONFIG_FOLDER, exist_ok=True)


THEME_STYLES = ("granite", "acrylic", "tinted", "clear")


def _migrate(config):
    """The shell's panel styles used to be "dark" and "glass" (see kiwi-shell's
    widgets/config.tsx): glass became Clear Glass, dark became Granite. The
    panels also had a light appearance once; they are dark only now."""
    if not config:
        return config
    config.pop("appearance", None)
    if config.get("theme") in THEME_STYLES:
        return config
    config["theme"] = "clear" if config.get("theme") == "glass" else "granite"
    return config


def _read():
    try:
        with open(CONFIG_FILE) as f:
            return _migrate(json.load(f))
    except (OSError, ValueError):
        return {}


_config = _read()
_pending = {}


def reload():
    """Pick up what kiwi-shell or `kiwi-settings auto-color` wrote meanwhile."""
    config = _read()
    config.update(_pending)
    _config.clear()
    _config.update(config)


def get(key):
    return _config.get(key, DEFAULTS.get(key))


def set(key, value):
    _config[key] = value
    _pending[key] = value


def write_conf():
    # Re-read first: kiwi-shell and `kiwi-settings auto-color` write the same
    # file, and their changes must survive ours.
    config = _read()
    config.update(_pending)
    _pending.clear()
    _config.clear()
    _config.update(config)

    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except OSError as e:
        print(f"Failed to save config: {e}")

    try:
        r, g, b = parse_color(get("primary_color"))
        hypr = (
            f"$kiwiColor = {_hypr_rgba(r, g, b, 1.0)}\n"
            f"$kiwiColorLight = {_hypr_rgba(r, g, b, BORDER_OPACITY)}\n"
        )
        with open(HYPR_FILE, "w") as f:
            f.write(hypr)
    except (OSError, ValueError) as e:
        print(f"Failed to save hypr colors: {e}")


def save(key, value):
    set(key, value)
    write_conf()


def parse_color(color: str):
    """#rrggbb or rgb(r, g, b) -> (r, g, b) in [0, 1]"""
    color = color.strip()
    if color.startswith("#") and len(color) == 7:
        return tuple(int(color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    match = re.fullmatch(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,[^)]*)?\)", color)
    if match:
        return tuple(int(c) / 255 for c in match.groups())
    raise ValueError(f"unsupported color: {color}")


def _hypr_rgba(r, g, b, a) -> str:
    return "rgba({:02x}{:02x}{:02x}{:02x})".format(
        round(r * 255), round(g * 255), round(b * 255), round(a * 255)
    )
