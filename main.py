from gi.repository import Adw

class AppearancePage(Adw.PreferencesPage):
    def __init__(self):
        super().__init__()
        self.set_icon_name("preferences-desktop-appearance-symbolic")

        group = Adw.PreferencesGroup(title="Theme")
        self.add(group)

        group.add(Adw.SwitchRow(title="Dark Mode"))
        # add more rows...