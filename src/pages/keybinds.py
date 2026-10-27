from gi.repository import Adw, GLib, Gtk

from config import get, save
from utils import shortcuts
from widgets.rows import nix_managed
from widgets.shortcut_dialog import ShortcutDialog

ROWS = [
    ("launcher", None),
    ("app_switcher", "Keep holding the modifier to go through your apps"),
    ("mission_control", "All your windows, and your desktops"),
    ("desktop_left", None),
    ("desktop_right", None),
    ("workspace_switcher", "Keep holding the modifier to go through your desktops"),
    ("notification_center", None),
]
# a kiwi-shell from before its binds sent global shortcuts described the
# launcher's as "kiwi: launcher toggle"
ACTIVE_DESCRIPTIONS = {
    "launcher": ("kiwi: launcher", "kiwi: launcher toggle"),
    "app_switcher": ("kiwi: apps open",),
    "mission_control": ("kiwi: mission control",),
    "desktop_left": ("kiwi: desktop left",),
    "desktop_right": ("kiwi: desktop right",),
    "workspace_switcher": ("kiwi: workspaces next",),
    "notification_center": ("kiwi: notification center",),
}
MEDIA_KEYS = ["kiwi: volume-up", "kiwi: volume-down", "kiwi: volume-mute"]


class KeybindsPage(Adw.PreferencesPage):
    def __init__(self):
        super().__init__()
        self._group = None
        self.refresh()

    def _current(self):
        value = get("shortcuts")
        return {name: shortcuts.configured(value, name) for name, _ in ROWS}

    def refresh(self, check=True):
        """check=False skips the "not active" check, while kiwi-shell is still rebinding."""
        if self._group:
            self.remove(self._group)

        binds = shortcuts.hyprland_binds()
        self._foreign = [b for b in binds or [] if b.get("submap") == "" and not shortcuts.is_kiwi_bind(b)]
        current = self._current()

        self._group = Adw.PreferencesGroup(
            title="Kiwi Shell",
            description="Select a keybind to change it, or + to add another.",
        )
        for name, note in ROWS:
            self._group.add(self._row(name, note, current, binds if check else None))

        media_row = Adw.ActionRow(title="Volume and Brightness Keys", subtitle="Show the on-screen indicator")
        if binds is not None:
            registered = {b.get("description") for b in binds}
            active = all(description in registered for description in MEDIA_KEYS)
            media_row.add_suffix(self._status(active))
        self._group.add(media_row)
        self.add(self._group)

    def _row(self, name, note, current, binds):
        found = current[name]
        subtitle = "Tap" if len(found) == 1 and found[0].tap else note
        row = Adw.ActionRow(title=shortcuts.TITLES[name], subtitle=subtitle or "", activatable=True)

        if found and binds is not None and not any(self._registered(binds, name, s) for s in found):
            row.set_subtitle("Not active: Kiwi Shell isn't running")

        if len(found) == 1:
            row.add_suffix(Gtk.ShortcutLabel(accelerator=found[0].accelerator(), valign=Gtk.Align.CENTER))
        # several: each its own button, to change or remove that one
        for shortcut in found if len(found) > 1 else []:
            button = Gtk.Button(
                child=Gtk.ShortcutLabel(accelerator=shortcut.accelerator()),
                valign=Gtk.Align.CENTER,
                css_classes=["flat", "keybind"],
                tooltip_text="Tap: change or remove" if shortcut.tap else "Change or remove",
            )
            button.connect("clicked", lambda _, s=shortcut: self._edit(name, current, s))
            row.add_suffix(button)
        if found:
            add = Gtk.Button(
                icon_name="list-add-symbolic",
                valign=Gtk.Align.CENTER,
                css_classes=["flat", "circular"],
                tooltip_text="Add Another Keybind",
            )
            add.connect("clicked", lambda _: self._edit(name, current, None))
            row.add_suffix(add)
        else:
            row.add_suffix(Gtk.Label(label="Not set", valign=Gtk.Align.CENTER, css_classes=["dim-label"]))
        row.add_suffix(Gtk.Image(icon_name="go-next-symbolic", css_classes=["dim-label"]))
        row.connect("activated", lambda _: self._edit(name, current, found[0] if found else None))
        return nix_managed(row, "shortcuts", name)

    @staticmethod
    def _registered(binds, name, shortcut):
        mask, key = shortcut.combos(name)[0]
        return any(
            b.get("description") in ACTIVE_DESCRIPTIONS[name]
            and b.get("modmask") == mask
            and str(b.get("key", "")).upper() == key
            for b in binds
        )

    @staticmethod
    def _status(active):
        return Gtk.Label(
            label="Active" if active else "Not active",
            valign=Gtk.Align.CENTER,
            css_classes=[] if active else ["dim-label"],
        )

    def _edit(self, name, current, shortcut):
        """Change `shortcut`, one of the action's, or add one when None."""
        others = {n: found for n, found in current.items() if n != name}
        siblings = [s for s in current[name] if s != shortcut]
        dialog = ShortcutDialog(
            name, shortcut, others, self._foreign,
            lambda response, new: self._chosen(name, current[name], shortcut, response, new),
            siblings,
        )
        dialog.present(self)

    def _chosen(self, name, found, old, response, new):
        if response == "reset":
            self._set(name, shortcuts.DEFAULT_SHORTCUTS[name])
            return
        found = list(found)
        if response == "remove":
            found.remove(old)
        elif old is None:
            found.append(new)
        else:
            found[found.index(old)] = new
        self._set(name, shortcuts.to_config(found))

    def _set(self, name, config_value):
        value = dict(shortcuts.DEFAULT_SHORTCUTS)
        value.update(get("shortcuts") or {})
        value[name] = config_value
        save("shortcuts", value)
        self.refresh(check=False)
        # kiwi-shell re-registers within a moment; show the result
        GLib.timeout_add(1000, self._refresh_once)

    def _refresh_once(self):
        self.refresh()
        return GLib.SOURCE_REMOVE
