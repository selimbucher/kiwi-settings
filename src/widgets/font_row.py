from gi.repository import Adw, Gtk, Pango

from config import get, save
from widgets.rows import nix_managed

QUICKSAND = "Quicksand"
# kiwi-shell's word for the desktop's own interface font
SYSTEM = "system"


def _system_family():
    name = Gtk.Settings.get_default().get_property("gtk-font-name") or ""
    return Pango.FontDescription.from_string(name).get_family() or "Sans"


class FontRow(Adw.ComboRow):
    """The shell's font: Quicksand, the desktop's own, or one picked from the
    installed fonts ("Other…", a font chooser), which is then on the list."""

    def __init__(self):
        super().__init__(title="Font", subtitle="Of the bar, dock and menus")
        self._quiet = False
        self._fonts = []
        self._show(get("font") or QUICKSAND)
        self.connect("notify::selected", self._on_selected)
        nix_managed(self, "font")

    def _show(self, font):
        """The list for `font`, it chosen in it."""
        self._fonts = [QUICKSAND, SYSTEM]
        labels = [QUICKSAND, f"System Font ({_system_family()})"]
        if font not in (QUICKSAND, SYSTEM):
            self._fonts.append(font)
            labels.append(font)
        self._fonts.append(None)  # Other…
        labels.append("Other…")
        self._quiet = True
        self.set_model(Gtk.StringList.new(labels))
        self.set_selected(self._fonts.index(font))
        self._quiet = False

    def _on_selected(self, row, _):
        if self._quiet:
            return
        font = self._fonts[row.get_selected()]
        if font is not None:
            save("font", font)
            return
        dialog = Gtk.FontDialog(title="Choose a Font")
        dialog.choose_family(row.get_root(), None, None, self._on_chosen)

    def _on_chosen(self, dialog, result):
        try:
            family = dialog.choose_family_finish(result)
            name = family.get_name() if family else None
        except Exception:
            name = None  # cancelled
        if name:
            save("font", name)
        # back to what it is now, picked or not
        self._show(get("font") or QUICKSAND)
