"""kiwi-shell's Hyprland plugin: what state it is in, and how to set it up.

The plugin is what lets the dock follow a window while it is dragged and the
switchers show their windows live instead of capturing them. It is compiled
against the Hyprland it loads into, so it has to be rebuilt after every
Hyprland update — which is what hyprpm, Hyprland's own plugin manager, is
for. Distributions that build kiwi-shell against their Hyprland (Nix) ship it
with the shell instead, and then there is nothing to do here.
"""

import json
import os
import shutil
import subprocess

REPO = "https://github.com/selimbucher/kiwi-shell"

# an older kiwi-shell carried the two halves as separate plugins
NAMES = ("kiwi", "geometry-events", "kiwi-previews")


def _data_home():
    return os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")


def loaded():
    """The kiwi plugins the compositor has, by name."""
    try:
        out = subprocess.run(
            ["hyprctl", "-j", "plugin", "list"], capture_output=True, text=True, timeout=5
        ).stdout
        return [p.get("name") for p in json.loads(out) if p.get("name") in NAMES]
    except (OSError, ValueError, subprocess.SubprocessError):
        return []


def managed():
    """Whether hyprpm is the one keeping it built."""
    return os.path.isdir(os.path.join(_data_home(), "hyprpm", "kiwi-shell"))


def have_hyprpm():
    return shutil.which("hyprpm") is not None


def state():
    """One of: active, installed, missing, unavailable — and whether hyprpm has it."""
    if loaded():
        return "active" if managed() else "shipped"
    if managed():
        return "installed"  # built, but not loaded into this session
    return "missing" if have_hyprpm() else "unavailable"


def setup_commands():
    """Everything hyprpm needs to do to get it running, in order."""
    return [
        ["hyprpm", "add", REPO],
        ["hyprpm", "enable", "kiwi"],
        ["hyprpm", "reload"],
    ]


def update_commands():
    return [["hyprpm", "update"], ["hyprpm", "reload"]]


def reload_commands():
    return [["hyprpm", "reload"]]
