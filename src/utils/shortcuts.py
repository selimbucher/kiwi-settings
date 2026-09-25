"""kiwi-shell's configurable shortcuts ("shortcuts" in config.json).

A shortcut is "Super", "Alt+Tab", "Super+space": modifiers joined with "+",
then a key name. A lone modifier means tapping it. This mirrors
kiwi-shell's src/kiwi-shell/shortcuts.ts.
"""

import json
import subprocess

from gi.repository import Gdk, Gtk

DEFAULT_SHORTCUTS = {
    "launcher": "Super",
    "app_switcher": "Alt+Tab",
    "workspace_switcher": "Super+Tab",
    "notification_center": "",
}

# name, GTK mask, Hyprland modmask bit, Hyprland name, the modifier's own keys
MODIFIERS = [
    ("Super", Gdk.ModifierType.SUPER_MASK, 64, "SUPER", ("Super_L", "Super_R")),
    ("Ctrl", Gdk.ModifierType.CONTROL_MASK, 4, "CTRL", ("Control_L", "Control_R")),
    ("Alt", Gdk.ModifierType.ALT_MASK, 8, "ALT", ("Alt_L", "Alt_R", "Meta_L", "Meta_R")),
    ("Shift", Gdk.ModifierType.SHIFT_MASK, 1, "SHIFT", ("Shift_L", "Shift_R")),
]
_BY_NAME = {name.lower(): (name, mask, bit, hypr, keys) for name, mask, bit, hypr, keys in MODIFIERS}


class Shortcut:
    def __init__(self, mods, key, tap):
        self.mods = mods  # canonical names, in MODIFIERS order: ["Super"]
        self.key = key  # GDK key name ("Tab", "space"); None for a tap
        self.tap = tap

    @classmethod
    def parse(cls, text):
        parts = [p.strip() for p in (text or "").split("+") if p.strip()]
        if not parts:
            return None
        mods = []
        for part in parts[:-1]:
            mod = _BY_NAME.get(part.lower())
            if not mod or mod[0] in mods:
                return None
            mods.append(mod[0])
        last = _BY_NAME.get(parts[-1].lower())
        if last:
            return cls([last[0]], None, True) if not mods else None
        if Gdk.keyval_from_name(parts[-1]) == Gdk.KEY_VoidSymbol:
            return None
        return cls(_ordered(mods), parts[-1], False)

    def __str__(self):
        return "+".join(self.mods + ([] if self.tap else [self.key]))

    def __eq__(self, other):
        return isinstance(other, Shortcut) and str(self).lower() == str(other).lower()

    def accelerator(self):
        mask = Gdk.ModifierType(0)
        for mod in self.mods:
            mask |= _BY_NAME[mod.lower()][1]
        keyval = 0 if self.tap else Gdk.keyval_from_name(self.key)
        return Gtk.accelerator_name(keyval, mask)

    def modmask(self):
        return sum(_BY_NAME[mod.lower()][2] for mod in self.mods)

    def combos(self, role):
        """(modmask, hyprland key) pairs kiwi binds for this shortcut in `role`"""
        mask = self.modmask()
        if self.tap:
            return [(mask, _BY_NAME[self.mods[0].lower()][4][0].upper())]
        key = self.key.upper()
        combos = [(mask, key)]
        if role == "workspace_switcher":
            combos.append((mask | 1, key))
        return combos


def _ordered(mods):
    return [name for name, *_ in MODIFIERS if name in mods]


def from_key_event(keyval, state):
    """A shortcut from a key press: modifiers held plus the key, or None for a modifier key."""
    name = Gdk.keyval_name(keyval)
    if any(name in keys for *_, keys in MODIFIERS):
        return None
    mods = [mod for mod, mask, *_ in MODIFIERS if state & mask]
    if state & Gdk.ModifierType.META_MASK and "Super" not in mods:
        mods.append("Super")
    return Shortcut(_ordered(mods), name, False)


def tap_for(keyval):
    name = Gdk.keyval_name(keyval)
    for mod, _, _, _, keys in MODIFIERS:
        if name in keys:
            return Shortcut([mod], None, True)
    return None


def configured(config_value, name):
    """The shortcut in use for `name`; None for an optional one that isn't set."""
    shortcut = Shortcut.parse((config_value or {}).get(name))
    if shortcut is None or problem(name, shortcut, {}) is not None:
        return Shortcut.parse(DEFAULT_SHORTCUTS[name])
    return shortcut


def problem(name, shortcut, others, foreign_binds=()):
    """Why `shortcut` can't be used for `name`, or None.

    others: the other shortcuts, {name: Shortcut}; foreign_binds: root binds
    from the Hyprland config, as reported by `hyprctl binds`.
    """
    if name in ("app_switcher", "workspace_switcher"):
        if shortcut.tap or len(shortcut.mods) != 1:
            return "Hold exactly one modifier while pressing a key, like Alt+Tab"
        if shortcut.mods == ["Shift"]:
            return "Shift is taken: it switches backwards"
    elif shortcut.tap and name != "launcher":
        return "Hold a modifier while pressing a key"
    elif not shortcut.tap and not shortcut.mods and not shortcut.key.startswith(("F", "XF86")):
        return "Add a modifier, or tap one on its own" if name == "launcher" else "Add a modifier"

    for other_name, other in others.items():
        if other_name == name or other is None:
            continue
        # a tap may share its modifier with a switcher; anything else can't overlap
        if shortcut.tap or other.tap:
            if shortcut.tap and other.tap and shortcut == other:
                return f"Already used by {TITLES[other_name]}"
            continue
        if set(shortcut.combos(name)) & set(other.combos(other_name)):
            return f"Already used by {TITLES[other_name]}"

    wanted = set(shortcut.combos(name))
    for bind in foreign_binds:
        if (bind.get("modmask"), str(bind.get("key", "")).upper()) in wanted:
            return "Already bound in your Hyprland config"
    return None


TITLES = {
    "launcher": "Open Launcher",
    "app_switcher": "Switch Apps",
    "workspace_switcher": "Switch Workspaces",
    "notification_center": "Show Notifications",
}


def hyprland_binds():
    """Every bind Hyprland reports, or None when it can't be asked."""
    try:
        result = subprocess.run(["hyprctl", "-j", "binds"], capture_output=True, text=True, timeout=2)
        return json.loads(result.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def is_kiwi_bind(bind):
    return bind.get("description", "").startswith("kiwi:")
