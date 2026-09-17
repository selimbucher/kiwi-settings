import os
import threading

from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from config import get, reload as reload_config, save
from utils.colors import get_color
from utils.wallpaper import get_wallpaper_path, set_wallpaper, wallpaper_folder
from widgets.hue_strip import HueStrip
from widgets.rows import combo_row
from widgets.style_switcher import StyleSwitcher, interface_settings
from widgets.wallpaper_grid import WallpaperGrid


class AppearancePage(Adw.PreferencesPage):
    def __init__(self):
        super().__init__()
        self._wallpaper = None

        settings = interface_settings()
        self._style = StyleSwitcher(settings) if settings else None
        if self._style:
            style_group = Adw.PreferencesGroup(title="Style")
            style_group.add(self._style)
            self.add(style_group)

        wallpaper_group = Adw.PreferencesGroup(title="Wallpaper")
        choose_button = Gtk.Button(label="Choose Picture…", valign=Gtk.Align.CENTER, css_classes=["flat"])
        choose_button.connect("clicked", self._on_choose_clicked)
        wallpaper_group.set_header_suffix(choose_button)
        self._grid = WallpaperGrid(on_selected=self._apply_wallpaper)
        wallpaper_group.add(self._grid)
        self.add(wallpaper_group)

        color_group = Adw.PreferencesGroup(title="Accent Color")
        self.add(color_group)

        color_row = Adw.ActionRow(title="Color", subtitle="Highlights in the bar, dock, menus and window borders")
        self._color_button = Gtk.Button(valign=Gtk.Align.CENTER, css_classes=["accent-dot"])
        self._accent_css = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), self._accent_css, Gtk.STYLE_PROVIDER_PRIORITY_USER + 2
        )

        popover = Gtk.Popover(position=Gtk.PositionType.BOTTOM)
        popover.set_parent(self._color_button)
        self._hue_strip = HueStrip(on_color_changed=self._on_color_picked)
        self._hue_strip.set_size_request(300, 80)
        self._hue_strip.set_margin_top(8)
        self._hue_strip.set_margin_bottom(8)
        self._hue_strip.set_margin_start(8)
        self._hue_strip.set_margin_end(8)
        popover.set_child(self._hue_strip)
        self._color_button.connect("clicked", lambda _: popover.popup())
        color_row.add_suffix(self._color_button)
        color_row.set_activatable_widget(self._color_button)
        color_group.add(color_row)

        match_row = Adw.SwitchRow(title="Match Wallpaper", subtitle="Take the accent color from the wallpaper")
        match_row.set_active(get("auto_color"))
        match_row.connect("notify::active", self._on_match_toggled)
        color_group.add(match_row)

        shell_group = Adw.PreferencesGroup(title="Shell")
        shell_group.add(
            combo_row(
                "theme",
                "Panel Style",
                [("dark", "Dark"), ("glass", "Glass")],
                subtitle="Background of the bar, dock and menus",
            )
        )
        self.add(shell_group)

        self._update_accent()
        self.refresh()

    def refresh(self):
        """Re-read what kiwi-shell or a terminal may have changed meanwhile."""
        reload_config()
        self._show_wallpaper(get_wallpaper_path())
        self._update_accent()

    def _show_wallpaper(self, path):
        self._wallpaper = path
        if self._style:
            self._style.set_wallpaper(path)
        self._grid.update(path)

    def _apply_wallpaper(self, path):
        path = os.path.realpath(path)
        set_wallpaper(path)
        self._show_wallpaper(path)
        if get("auto_color"):
            self._match_accent(path)

    def _on_choose_clicked(self, button):
        images = Gtk.FileFilter(name="Images")
        images.add_pixbuf_formats()
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(images)
        dialog = Gtk.FileDialog(
            title="Choose a Wallpaper",
            filters=filters,
            default_filter=images,
            initial_folder=Gio.File.new_for_path(wallpaper_folder(self._wallpaper)),
        )
        dialog.open(button.get_root(), None, self._on_chosen)

    def _on_chosen(self, dialog, result):
        try:
            file = dialog.open_finish(result)
        except GLib.Error:
            return  # cancelled
        if file and file.get_path():
            self._apply_wallpaper(file.get_path())

    def _match_accent(self, path):
        def work():
            color = get_color(path)
            if color:
                GLib.idle_add(self._set_accent, color)

        threading.Thread(target=work, daemon=True).start()

    def _set_accent(self, color):
        save("primary_color", color)
        self._update_accent()
        return GLib.SOURCE_REMOVE

    def _update_accent(self):
        color = get("primary_color")
        self._accent_css.load_from_string(f".accent-dot {{ background-color: {color}; }}")
        self._hue_strip.set_color(color)

    def _on_color_picked(self, hex_color):
        save("primary_color", hex_color)
        self._update_accent()

    def _on_match_toggled(self, row, _):
        save("auto_color", row.get_active())
        if row.get_active() and self._wallpaper:
            self._match_accent(self._wallpaper)
