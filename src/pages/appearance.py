from gi.repository import Adw, Gtk, Gdk, Gio
from config import get, set as set_conf, write_conf
from widgets.hue_strip import HueStrip


class AppearancePage(Adw.PreferencesPage):
    def __init__(self):
        super().__init__()
        self.set_icon_name("preferences-desktop-appearance-symbolic")

        self._desktop_settings = Gio.Settings(schema="org.gnome.desktop.interface")

        theme_group = Adw.PreferencesGroup(title="Theme")
        self.add(theme_group)

        dark_row = Adw.SwitchRow(title="Dark Mode")
        dark_row.set_active(
            self._desktop_settings.get_string("color-scheme") == "prefer-dark"
        )
        dark_row.connect("notify::active", self.on_dark_mode_changed)
        theme_group.add(dark_row)

        options = Gtk.StringList.new(["Dark", "Glass"])
        theme_row = Adw.ComboRow(title="Kiwi Theme", model=options)
        themes = ["dark", "glass"]
        theme = get("theme", "dark")
        theme_row.set_selected(themes.index(theme) if theme in themes else 0)
        theme_row.connect("notify::selected", self.on_theme_changed)
        theme_group.add(theme_row)

        color_group = Adw.PreferencesGroup(title="Color")
        self.add(color_group)

        color_row = Adw.ActionRow(title="Accent Color")
        self._color_button = Gtk.Button()
        self._color_button.set_valign(Gtk.Align.CENTER)
        self._color_button.add_css_class("circular")
        self._update_color_button()

        popover = Gtk.Popover()
        popover.set_parent(self._color_button)
        popover.set_position(Gtk.PositionType.BOTTOM)
        popover.set_has_arrow(True)

        pop_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            margin_top=8,
            margin_bottom=8,
            margin_start=8,
            margin_end=8,
        )
        self.hue_strip = HueStrip(on_color_changed=self.on_color_changed)
        self.hue_strip.set_size_request(300, 80)
        pop_box.append(self.hue_strip)
        popover.set_child(pop_box)

        self._color_button.connect("clicked", lambda _: popover.popup())
        color_row.add_suffix(self._color_button)
        color_row.set_activatable_widget(self._color_button)
        color_group.add(color_row)

    def _update_color_button(self):
        hex_color = get("primary_color", "#ffffff")
        css = Gtk.CssProvider()
        css.load_from_string(f"""
            .color-dot {{
                background-color: {hex_color};
                min-width: 24px;
                min-height: 24px;
            }}
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        self._color_button.add_css_class("color-dot")

    def on_color_changed(self, hue, lightness):
        r, g, b = HueStrip._hsl_to_rgb(None, hue, HueStrip.S, lightness)
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(r * 255), int(g * 255), int(b * 255)
        )
        set_conf("primary_color", hex_color)
        write_conf()
        self._update_color_button()

    def on_dark_mode_changed(self, row, _):
        self._desktop_settings.set_string(
            "color-scheme",
            "prefer-dark" if row.get_active() else "default"
        )

    def on_theme_changed(self, row, _):
        set_conf("theme", row.get_selected_item().get_string().lower())
        write_conf()