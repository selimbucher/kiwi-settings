from gi.repository import Adw, Gtk

from config import DEFAULTS, get, save
from widgets.rows import combo_row, spin_row

CENTERS = [("desktops", "Desktops"), ("date", "Date"), ("weather", "Weather"), ("none", "Nothing")]
UNITS = [("celsius", "Celsius"), ("fahrenheit", "Fahrenheit")]


def island():
    """The island's settings, the defaults filled in."""
    return {**DEFAULTS["island"], **(get("island") or {})}


def save_island(key, value):
    settings = island()
    settings[key] = value
    save("island", settings)


def island_combo(key, title, options, subtitle=None):
    values = [value for value, _ in options]
    row = Adw.ComboRow(
        title=title,
        subtitle=subtitle or "",
        model=Gtk.StringList.new([label for _, label in options]),
    )
    current = island()[key]
    row.set_selected(values.index(current) if current in values else 0)
    row.connect("notify::selected", lambda r, _: save_island(key, values[r.get_selected()]))
    return row


def island_switch(key, title, subtitle):
    row = Adw.SwitchRow(title=title, subtitle=subtitle)
    row.set_active(bool(island()[key]))
    row.connect("notify::active", lambda r, _: save_island(key, r.get_active()))
    return row


class BarPage(Adw.PreferencesPage):
    def __init__(self):
        super().__init__()

        bar_group = Adw.PreferencesGroup(title="Status Bar")
        bar_group.add(spin_row("bar_margin", "Margin", 0, 12, "Gap to tiled windows, in pixels"))
        self.add(bar_group)

        island_group = Adw.PreferencesGroup(
            title="Dynamic Island",
            description="The middle of the bar, and what it shows while something goes on",
        )
        center = island_combo("center", "Middle", CENTERS, "What the island shows at rest")
        island_group.add(center)

        city = Adw.EntryRow(title="City", show_apply_button=True)
        city.set_text(island()["weather_city"] or "")
        city.connect("apply", lambda r: save_island("weather_city", r.get_text().strip()))
        island_group.add(city)
        units = island_combo("weather_units", "Units", UNITS)
        island_group.add(units)

        def weather_rows(*_):
            on = CENTERS[center.get_selected()][0] == "weather"
            city.set_visible(on)
            units.set_visible(on)

        center.connect("notify::selected", weather_rows)
        weather_rows()

        shown = Adw.ActionRow(title="Activities and Alerts", subtitle="What may show up in the island", activatable=True)
        shown.add_suffix(Gtk.Image.new_from_icon_name("go-next-symbolic"))
        shown.connect("activated", lambda _: IslandEventsDialog().present(self.get_root()))
        island_group.add(shown)
        self.add(island_group)

        indicator_group = Adw.PreferencesGroup(
            title="Volume and Brightness",
            description="The indicator shown while changing either",
        )
        indicator_group.add(
            combo_row("indicator_bar_position", "Position", [("bottom", "Bottom"), ("left", "Left")])
        )
        self.add(indicator_group)


class IslandEventsDialog(Adw.PreferencesDialog):
    """Which activities and alerts the island shows."""

    def __init__(self):
        super().__init__(title="Activities and Alerts", content_width=520, content_height=560)
        page = Adw.PreferencesPage()

        activities = Adw.PreferencesGroup(
            title="Activities",
            description="Shown for as long as they go on. The microphone, camera and screen dots always show.",
        )
        activities.add(island_switch("now_playing", "Now Playing", "Music and videos playing"))
        activities.add(island_switch("performance", "Performance", "Memory running out, the CPU hot or busy for minutes"))
        page.add(activities)

        alerts = Adw.PreferencesGroup(title="Alerts", description="Shown for a few seconds")
        alerts.add(island_switch("devices", "Bluetooth Devices", "A device connecting, with its battery"))
        alerts.add(island_switch("charging", "Charging", "The charger plugged in"))
        alerts.add(island_switch("focus", "Do Not Disturb", "Turned on or off"))
        page.add(alerts)

        self.add(page)
