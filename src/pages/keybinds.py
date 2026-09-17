from gi.repository import Adw, GLib, Gtk

from config import get, save
from utils import shortcuts
from widgets.shortcut_dialog import ShortcutDialog

ROWS = [
    ("launcher", None),
    ("app_switcher", "Keep holding the modifier to go through your apps"),
    ("workspace_switcher", "Add Shift to go backwards"),
]
ACTIVE_DESCRIPTIONS = {
    "launcher": "kiwi: launcher toggle",
    "app_switcher": "kiwi: apps open",
    "workspace_switcher": "kiwi: workspaces next",
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
            description="Select a keybind to change it.",
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
        shortcut = current[name]
        subtitle = "Tap" if shortcut.tap else note
        row = Adw.ActionRow(title=shortcuts.TITLES[name], subtitle=subtitle or "", activatable=True)

        if binds is not None and not self._registered(binds, name, shortcut):
            row.set_subtitle("Not active: Kiwi Shell isn't running, or your Hyprland config already uses these keys")

        row.add_suffix(Gtk.ShortcutLabel(accelerator=shortcut.accelerator(), valign=Gtk.Align.CENTER))
        row.add_suffix(Gtk.Image(icon_name="go-next-symbolic", css_classes=["dim-label"]))
        row.connect("activated", lambda _: self._edit(name, current))
        return row

    @staticmethod
    def _registered(binds, name, shortcut):
        mask, key = shortcut.combos(name)[0]
        return any(
            b.get("description") == ACTIVE_DESCRIPTIONS[name]
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

    def _edit(self, name, current):
        others = {n: s for n, s in current.items() if n != name}
        dialog = ShortcutDialog(name, current[name], others, self._foreign, lambda s: self._set(name, s))
        dialog.present(self)

    def _set(self, name, shortcut):
        value = dict(shortcuts.DEFAULT_SHORTCUTS)
        value.update(get("shortcuts") or {})
        value[name] = str(shortcut)
        save("shortcuts", value)
        self.refresh(check=False)
        # kiwi-shell re-registers within a moment; show the result
        GLib.timeout_add(1000, self._refresh_once)

    def _refresh_once(self):
        self.refresh()
        return GLib.SOURCE_REMOVE
