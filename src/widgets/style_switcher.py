from gi.repository import Gio, Gtk

from widgets.thumbnail import Thumbnail

INTERFACE_SCHEMA = "org.gnome.desktop.interface"


def interface_settings():
    """org.gnome.desktop.interface, or None where the schema isn't installed.

    Its color-scheme key is the system appearance: xdg-desktop-portal serves it
    to GTK, Qt, browsers and Electron apps.
    """
    source = Gio.SettingsSchemaSource.get_default()
    if source is None or source.lookup(INTERFACE_SCHEMA, True) is None:
        return None
    return Gio.Settings(schema_id=INTERFACE_SCHEMA)


class StyleSwitcher(Gtk.Box):
    """Light and Dark tiles: the wallpaper with two windows in that style."""

    def __init__(self, settings):
        super().__init__(spacing=24, halign=Gtk.Align.CENTER, homogeneous=True)
        self.add_css_class("style-switcher")
        self._settings = settings
        self._syncing = False

        self._previews = []
        self._light = self._tile("Light", "light")
        self._dark = self._tile("Dark", "dark")
        self._dark.set_group(self._light)
        self.append(self._light)
        self.append(self._dark)

        self._sync()
        settings.connect("changed::color-scheme", lambda *_: self._sync())

    def set_wallpaper(self, path):
        for preview in self._previews:
            preview.set_path(path)

    def _tile(self, label, style):
        overlay = Gtk.Overlay(css_classes=["style-preview"])
        preview = Thumbnail(176, 110, "style-wallpaper")
        self._previews.append(preview)
        overlay.set_child(preview)
        overlay.add_overlay(self._window(style, "back", Gtk.Align.START, Gtk.Align.START))
        overlay.add_overlay(self._window(style, "front", Gtk.Align.END, Gtk.Align.END))

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.append(overlay)
        box.append(Gtk.Label(label=label))

        button = Gtk.ToggleButton(child=box, css_classes=["flat", "style-tile"])
        button.connect("toggled", self._on_toggled, style)
        return button

    def _window(self, style, depth, halign, valign):
        titlebar = Gtk.Box(spacing=3, css_classes=["style-titlebar"])
        for button in ("close", "minimize", "maximize"):
            titlebar.append(Gtk.Box(valign=Gtk.Align.CENTER, css_classes=["style-dot", button]))
        window = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            halign=halign,
            valign=valign,
            css_classes=["style-window", style, depth],
        )
        window.append(titlebar)
        window.append(Gtk.Box(vexpand=True))
        return window

    def _sync(self):
        dark = self._settings.get_string("color-scheme") == "prefer-dark"
        self._syncing = True
        (self._dark if dark else self._light).set_active(True)
        self._syncing = False

    def _on_toggled(self, button, style):
        if self._syncing or not button.get_active():
            return
        scheme = "prefer-dark" if style == "dark" else "prefer-light"
        current_dark = self._settings.get_string("color-scheme") == "prefer-dark"
        if current_dark != (style == "dark"):
            self._settings.set_string("color-scheme", scheme)
