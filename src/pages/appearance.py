from gi.repository import Adw, Gtk, Gdk
from config import get, set as set_conf, write_conf
from widgets.hue_strip import HueStrip


class AppearancePage(Adw.PreferencesPage):
    def __init__(self):
        super().__init__()
        self.set_icon_name("preferences-desktop-appearance-symbolic")

        kiwi_group = Adw.PreferencesGroup(title="Kiwi Shell")
        self.add(kiwi_group)

        kiwi_options = Gtk.StringList.new(["Dark", "Glass"])
        kiwi_theme_row = Adw.ComboRow(title="Theme", model=kiwi_options)
        kiwi_themes = ["dark", "glass"]
        kiwi_theme = get("theme", "dark")
        kiwi_theme_row.set_selected(kiwi_themes.index(kiwi_theme) if kiwi_theme in kiwi_themes else 0)
        kiwi_theme_row.connect("notify::selected", self.on_kiwi_theme_changed)
        kiwi_group.add(kiwi_theme_row)

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

    def on_kiwi_theme_changed(self, row, _):
        set_conf("theme", row.get_selected_item().get_string().lower())
        write_conf()