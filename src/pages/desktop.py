from gi.repository import Adw, Gtk
from config import get, set as set_conf, write_conf


class DesktopPage(Adw.PreferencesPage):
    def __init__(self):
        super().__init__()
        self.set_icon_name("user-desktop-symbolic")

        group = Adw.PreferencesGroup(title="Desktop")

        icons_row = Adw.SwitchRow(
            title="Desktop Icons",
            subtitle="Show the files in your Desktop folder behind all windows",
        )
        icons_row.set_active(get("desktop_icons", True))
        icons_row.connect("notify::active", lambda row, _: [set_conf("desktop_icons", row.get_active()), write_conf()])
        group.add(icons_row)

        placement_row = Adw.SwitchRow(
            title="Free Placement",
            subtitle="Icons stay on the grid spot you drag them to instead of auto-arranging",
        )
        placement_row.set_active(get("desktop_free_placement", True))
        placement_row.connect("notify::active", lambda row, _: [set_conf("desktop_free_placement", row.get_active()), write_conf()])
        group.add(placement_row)

        self.add(group)

        monitor_group = Adw.PreferencesGroup(title="Multi-Monitor")

        options = Gtk.StringList.new(["Active Monitor", "Main Monitor"])
        popup_row = Adw.ComboRow(
            title="Show Popups On",
            subtitle="Where switchers, the launcher and notifications appear",
            model=options,
        )
        popup_values = ["active", "primary"]
        current = get("popup_monitor", "active")
        popup_row.set_selected(popup_values.index(current) if current in popup_values else 0)
        popup_row.connect(
            "notify::selected",
            lambda row, _: [set_conf("popup_monitor", popup_values[row.get_selected()]), write_conf()],
        )
        monitor_group.add(popup_row)

        self.add(monitor_group)
