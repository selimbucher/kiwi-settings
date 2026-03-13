from gi.repository import Adw
from config import get, set as set_conf

class DockPage(Adw.PreferencesPage):
    def __init__(self):
        super().__init__()
        self.set_icon_name("xapp-prefs-toolbar-symbolic")

        group = Adw.PreferencesGroup(title="Dock Items")

        home_row = Adw.SwitchRow(title="Home Folder")
        home_row.set_active(get("dock_home", True))
        home_row.connect("notify::active", lambda row, _: set_conf("dock_home", row.get_active()))
        group.add(home_row)

        trash_row = Adw.SwitchRow(title="Trash")
        trash_row.set_active(get("dock_trash", True))
        trash_row.connect("notify::active", lambda row, _: set_conf("dock_trash", row.get_active()))
        group.add(trash_row)

        self.add(group)