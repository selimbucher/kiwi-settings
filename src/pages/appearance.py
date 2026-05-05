from gi.repository import Adw, Gtk, Gdk
from config import get, set as set_conf, write_conf
from widgets.hue_strip import HueStrip

from utils.colors import get_color
from utils.wallpaper import get_wallpaper_path

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
        color_group.add(color_row)

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


        
        autocolor_row = Adw.SwitchRow(title="Match Wallpaper", subtitle="Automatically adjust colors to match your wallpaper")
        autocolor_row.set_active(get("auto_color", False))
        autocolor_row.connect("notify::active", self._on_autocolor_toggled)
        color_group.add(autocolor_row)





        nightshift_group = Adw.PreferencesGroup(title="Night Shift")
        self.add(nightshift_group)

        auto_nightshift_row = Adw.SwitchRow(
            title="Schedule Night Shift",
            subtitle="Automatically enable within a timeframe",
        )
        auto_nightshift_row.set_active(get("auto_nightshift", False))
        auto_nightshift_row.connect("notify::active", self._on_auto_nightshift_toggled)
        nightshift_group.add(auto_nightshift_row)

        # Track dependent rows so we can grey them out when scheduling is off
        self._nightshift_dependents = []

        # From
        from_row = Adw.ActionRow(title="From")
        self._from_button = Gtk.Button(valign=Gtk.Align.CENTER)
        self._from_button.add_css_class("flat")
        self._from_button.set_label(get("nightshift_start", "22:00"))
        self._from_button.connect(
            "clicked",
            lambda btn: self._open_time_popover(btn, "nightshift_start"),
        )
        from_row.add_suffix(self._from_button)
        from_row.set_activatable_widget(self._from_button)
        nightshift_group.add(from_row)
        self._nightshift_dependents.append(from_row)

        # To
        to_row = Adw.ActionRow(title="To")
        self._to_button = Gtk.Button(valign=Gtk.Align.CENTER)
        self._to_button.add_css_class("flat")
        self._to_button.set_label(get("nightshift_end", "06:00"))
        self._to_button.connect(
            "clicked",
            lambda btn: self._open_time_popover(btn, "nightshift_end"),
        )
        to_row.add_suffix(self._to_button)
        to_row.set_activatable_widget(self._to_button)
        nightshift_group.add(to_row)
        self._nightshift_dependents.append(to_row)

        # Intensity
        intensity_row = Adw.ActionRow(title="Intensity")

        intensity_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=8,
            valign=Gtk.Align.CENTER,
        )

        warm_icon = Gtk.Image.new_from_icon_name("temperature-symbolic")
        warm_icon.add_css_class("dim-label")

        cold_icon = Gtk.Image.new_from_icon_name("weather-snow-night-symbolic")
        cold_icon.add_css_class("dim-label")

        intensity_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 3000, 6000, 100)
        intensity_scale.set_inverted(True)
        intensity_scale.set_value(get("nightshift_intensity", 4000))
        intensity_scale.set_size_request(200, -1)
        intensity_scale.set_valign(Gtk.Align.CENTER)
        intensity_scale.set_draw_value(False)
        intensity_scale.connect("value-changed", self._on_intensity_changed)

        intensity_box.append(cold_icon)
        intensity_box.append(intensity_scale)
        intensity_box.append(warm_icon)
        

        intensity_row.add_suffix(intensity_box)
        nightshift_group.add(intensity_row)

        # Apply initial sensitivity based on switch state
        self._update_nightshift_sensitivity(auto_nightshift_row.get_active())



    def _on_autocolor_toggled(self, row, _):
        set_conf("auto_color", row.get_active())
        write_conf()
        if row.get_active():
            wallpaper_path = get_wallpaper_path()
            if wallpaper_path:
                color = get_color(wallpaper_path)
                set_conf("primary_color", color)
                write_conf()
                self._update_color_button()

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

    def _on_auto_nightshift_toggled(self, row, _):
        active = row.get_active()
        set_conf("auto_nightshift", active)
        write_conf()
        self._update_nightshift_sensitivity(active)

    def _update_nightshift_sensitivity(self, active):
        for row in self._nightshift_dependents:
            row.set_sensitive(active)

    def _on_intensity_changed(self, scale):
        set_conf("nightshift_intensity", int(scale.get_value()))
        write_conf()

    def _open_time_popover(self, button, config_key):
        try:
            h_str, m_str = get(config_key, "00:00").split(":")
            hour, minute = int(h_str), int(m_str)
        except (ValueError, AttributeError):
            hour, minute = 0, 0

        popover = Gtk.Popover()
        popover.set_parent(button)
        popover.set_position(Gtk.PositionType.BOTTOM)
        popover.set_has_arrow(True)
        popover.connect("closed", lambda p: p.unparent())

        box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=4,
            margin_top=8,
            margin_bottom=8,
            margin_start=8,
            margin_end=8,
        )

        hour_spin = Gtk.SpinButton.new_with_range(0, 23, 1)
        hour_spin.set_value(hour)
        hour_spin.set_wrap(True)
        hour_spin.set_orientation(Gtk.Orientation.VERTICAL)

        colon = Gtk.Label(label=":")
        colon.set_valign(Gtk.Align.CENTER)

        minute_spin = Gtk.SpinButton.new_with_range(0, 59, 1)
        minute_spin.set_value(minute)
        minute_spin.set_wrap(True)
        minute_spin.set_orientation(Gtk.Orientation.VERTICAL)

        def on_change(_=None):
            time_str = f"{int(hour_spin.get_value()):02d}:{int(minute_spin.get_value()):02d}"
            button.set_label(time_str)
            set_conf(config_key, time_str)
            write_conf()

        hour_spin.connect("value-changed", on_change)
        minute_spin.connect("value-changed", on_change)

        box.append(hour_spin)
        box.append(colon)
        box.append(minute_spin)

        popover.set_child(box)
        popover.popup()