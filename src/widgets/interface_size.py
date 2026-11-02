import json

from gi.repository import Adw, Gdk, Gtk

from config import get, save
from utils.shell import ask
from widgets.rows import nix_managed

SIZES = [1.0, 1.25, 1.5, 1.75, 2.0]


def _percent(size):
    return f"{round(size * 100)}%"


def _own_displays():
    """The displays as this app sees them, for when the shell can't say:
    keyed as the shell keys them (widgets/zoom.tsx, displayKey)."""
    displays = []
    monitors = Gdk.Display.get_default().get_monitors()
    for i in range(monitors.get_n_items()):
        monitor = monitors.get_item(i)
        connector = monitor.get_connector() or ""
        key = " ".join(p for p in (monitor.get_manufacturer(), monitor.get_model()) if p) or connector
        built_in = connector.upper().startswith(("EDP", "LVDS", "DSI"))
        displays.append({"key": key, "name": "Built-in Display" if built_in else key, "auto": None})
    return displays


class InterfaceSizeGroup(Adw.PreferencesGroup):
    """kiwi's own size on each display, apart from the apps' scale: by itself
    (what the shell works out for the display) or a size chosen here."""

    def __init__(self):
        super().__init__(
            title="Interface Size",
            description="The bar, dock and menus, apart from apps. Automatic fits them to each display.",
        )
        self._rows = []
        # the shell's word on the displays, with the size it takes on each
        ask(["displays"], self._fill)

    def _fill(self, answer):
        try:
            displays = json.loads(answer) if answer else None
        except ValueError:
            displays = None
        for display in displays or _own_displays():
            self._add(display)

    def _add(self, display):
        key = display["key"]
        chosen = (get("interface_scale") or {}).get(key)
        sizes = list(SIZES)
        if isinstance(chosen, (int, float)) and chosen not in sizes:
            sizes = sorted(sizes + [chosen])
        auto = display.get("auto")
        labels = [f"Automatic ({_percent(auto)})" if auto else "Automatic"] + [_percent(s) for s in sizes]
        row = Adw.ComboRow(title=display["name"], model=Gtk.StringList.new(labels))
        row.set_selected(sizes.index(chosen) + 1 if chosen in sizes else 0)

        def changed(r, _):
            scales = dict(get("interface_scale") or {})
            index = r.get_selected()
            if index == 0:
                scales.pop(key, None)
            else:
                scales[key] = sizes[index - 1]
            save("interface_scale", scales)

        row.connect("notify::selected", changed)
        self.add(nix_managed(row, "interface_scale", key))
        self._rows.append(row)
