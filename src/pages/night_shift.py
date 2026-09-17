from gi.repository import Adw, GLib, Gtk

from config import get, save
from widgets.rows import switch_row


class NightShiftPage(Adw.PreferencesPage):
    def __init__(self):
        super().__init__()

        group = Adw.PreferencesGroup(
            title="Night Shift",
            description="Warmer colors in the evening. The toggle in the system menu works at any time.",
        )
        self.add(group)

        schedule_row = switch_row("auto_nightshift", "Schedule", "Turn on automatically between these times")
        schedule_row.connect("notify::active", lambda row, _: self._update_sensitivity(row.get_active()))
        group.add(schedule_row)

        self._schedule_rows = [
            self._time_row("From", "nightshift_start"),
            self._time_row("To", "nightshift_end"),
        ]
        for row in self._schedule_rows:
            group.add(row)

        intensity_row = Adw.ActionRow(title="Intensity")
        intensity_box = Gtk.Box(spacing=8, valign=Gtk.Align.CENTER)
        cold_icon = Gtk.Image(icon_name="weather-snow-night-symbolic", css_classes=["dim-label"])
        warm_icon = Gtk.Image(icon_name="temperature-symbolic", css_classes=["dim-label"])
        # color temperature in kelvin: lower is warmer, so the scale runs backwards
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 3000, 6000, 100)
        scale.set_inverted(True)
        scale.set_draw_value(False)
        scale.set_size_request(200, -1)
        scale.set_value(get("nightshift_intensity"))
        scale.connect("value-changed", lambda s: save("nightshift_intensity", int(s.get_value())))
        intensity_box.append(cold_icon)
        intensity_box.append(scale)
        intensity_box.append(warm_icon)
        intensity_row.add_suffix(intensity_box)
        group.add(intensity_row)

        self._update_sensitivity(schedule_row.get_active())

    def _time_row(self, title, key):
        row = Adw.ActionRow(title=title)
        button = Gtk.Button(label=get(key), valign=Gtk.Align.CENTER, css_classes=["flat", "numeric"])
        button.connect("clicked", self._open_time_popover, key)
        row.add_suffix(button)
        row.set_activatable_widget(button)
        return row

    def _update_sensitivity(self, active):
        for row in self._schedule_rows:
            row.set_sensitive(active)

    def _open_time_popover(self, button, key):
        try:
            hour, minute = (int(part) for part in get(key).split(":"))
        except (ValueError, AttributeError):
            hour, minute = 0, 0

        popover = Gtk.Popover(position=Gtk.PositionType.BOTTOM)
        popover.set_parent(button)
        popover.connect("closed", lambda p: GLib.idle_add(p.unparent))

        box = Gtk.Box(spacing=4, margin_top=8, margin_bottom=8, margin_start=8, margin_end=8)
        hour_spin = Gtk.SpinButton.new_with_range(0, 23, 1)
        minute_spin = Gtk.SpinButton.new_with_range(0, 59, 1)
        for spin, value in ((hour_spin, hour), (minute_spin, minute)):
            spin.set_value(value)
            spin.set_wrap(True)
            spin.set_orientation(Gtk.Orientation.VERTICAL)

        def on_change(_):
            time = f"{int(hour_spin.get_value()):02d}:{int(minute_spin.get_value()):02d}"
            button.set_label(time)
            save(key, time)

        hour_spin.connect("value-changed", on_change)
        minute_spin.connect("value-changed", on_change)

        box.append(hour_spin)
        box.append(Gtk.Label(label=":", valign=Gtk.Align.CENTER))
        box.append(minute_spin)
        popover.set_child(box)
        popover.popup()
