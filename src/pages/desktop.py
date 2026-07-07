from gi.repository import Adw
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

        self.add(group)
