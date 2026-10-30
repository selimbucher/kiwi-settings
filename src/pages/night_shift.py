from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from config import get, managed, save
from widgets.rows import nix_managed

SCHEDULES = [("off", "Off"), ("sunset", "Sunset to Sunrise"), ("custom", "Custom")]


def _preview(kelvin):
    """The warmth shown on screen at once, on or off, while it is chosen; None
    for the choosing done. Asked of the running shell (its request over D-Bus,
    as kiwictl asks), not written to the settings at every step of a drag."""
    args = ["night-shift-preview", "end" if kelvin is None else str(int(kelvin))]
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        bus.call("io.Astal.ags", "/io/Astal/Application", "io.Astal.Application", "Request",
                 GLib.Variant("(as)", (args,)), GLib.VariantType("(s)"), Gio.DBusCallFlags.NONE,
                 1000, None, lambda b, r: _finish(b, r))
    except GLib.Error:
        pass


def _finish(bus, result):
    try:
        bus.call_finish(result)
    except GLib.Error:
        pass  # the shell isn't running: nothing to show it on


class NightShiftPage(Adw.PreferencesPage):
    def __init__(self):
        super().__init__()

        group = Adw.PreferencesGroup(
            title="Night Shift",
            description="Warmer colors in the evening. The switch in the system menu turns it on or off "
            "until the schedule's next start or end.",
        )
        self.add(group)

        values = [value for value, _ in SCHEDULES]
        schedule_row = Adw.ComboRow(
            title="Schedule",
            model=Gtk.StringList.new([label for _, label in SCHEDULES]),
        )
        current = "off" if not get("auto_nightshift") else ("sunset" if get("nightshift_schedule") == "sunset" else "custom")
        schedule_row.set_selected(values.index(current))
        schedule_row.connect("notify::selected", lambda row, _: self._schedule_changed(values[row.get_selected()]))
        nix_managed(schedule_row, "nightshift_schedule" if managed("nightshift_schedule") else "auto_nightshift")
        group.add(schedule_row)
        self._schedule_row = schedule_row

        self._schedule_rows = [
            self._time_row("From", "nightshift_start"),
            self._time_row("To", "nightshift_end"),
        ]
        for row in self._schedule_rows:
            group.add(row)

        # Less warm to the left, as a Mac has it: the scale counts kelvin, lower
        # warmer, so it runs backwards. Shown on the screen while dragged, on or
        # off, and kept once let go of.
        warmth_row = Adw.ActionRow(title="Color Temperature")
        warmth_box = Gtk.Box(spacing=8, valign=Gtk.Align.CENTER)
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 3000, 6000, 100)
        scale.set_inverted(True)
        scale.set_draw_value(False)
        scale.set_size_request(180, -1)
        scale.set_value(get("nightshift_intensity"))
        warmth_box.append(Gtk.Label(label="Less Warm", css_classes=["dim-label", "caption"]))
        warmth_box.append(scale)
        warmth_box.append(Gtk.Label(label="More Warm", css_classes=["dim-label", "caption"]))
        warmth_row.add_suffix(warmth_box)
        group.add(nix_managed(warmth_row, "nightshift_intensity"))
        self._warmth(scale)

        self._update_sensitivity(current)

    def _warmth(self, scale):
        state = {"held": False, "settle": 0}

        def commit():
            state["settle"] = 0
            save("nightshift_intensity", int(scale.get_value()))
            _preview(None)
            return GLib.SOURCE_REMOVE

        def changed(_):
            _preview(scale.get_value())
            # by the keys or the wheel, no button to let go of: kept a moment after
            if not state["held"]:
                if state["settle"]:
                    GLib.source_remove(state["settle"])
                state["settle"] = GLib.timeout_add(700, commit)

        def event(controller, _ev):
            # (PyGObject passes the event itself as None)
            ev = controller.get_current_event()
            if ev is None:
                return False
            kind = ev.get_event_type()
            if kind in (Gdk.EventType.BUTTON_PRESS, Gdk.EventType.TOUCH_BEGIN):
                state["held"] = True
            elif kind in (Gdk.EventType.BUTTON_RELEASE, Gdk.EventType.TOUCH_END, Gdk.EventType.TOUCH_CANCEL):
                if state["held"]:
                    state["held"] = False
                    commit()
            return False

        scale.connect("value-changed", changed)
        watch = Gtk.EventControllerLegacy(propagation_phase=Gtk.PropagationPhase.CAPTURE)
        watch.connect("event", event)
        scale.add_controller(watch)
        # the window closed mid-drag: the screen goes back to what it is
        scale.connect("unrealize", lambda _: commit() if state["held"] or state["settle"] else None)

    def _schedule_changed(self, value):
        if value == "off":
            save("auto_nightshift", False)
        else:
            save("nightshift_schedule", value)
            save("auto_nightshift", True)
        self._update_sensitivity(value)

    def _time_row(self, title, key):
        row = Adw.ActionRow(title=title)
        button = Gtk.Button(label=get(key), valign=Gtk.Align.CENTER, css_classes=["flat", "numeric"])
        button.connect("clicked", self._open_time_popover, key)
        row.add_suffix(button)
        row.set_activatable_widget(button)
        return row

    def _update_sensitivity(self, schedule):
        for row in self._schedule_rows:
            row.set_visible(schedule == "custom")
        if self._schedule_row.get_sensitive():
            self._schedule_row.set_subtitle(
                "Where your time zone is, or the weather city when one is set"
                if schedule == "sunset" else "")

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
