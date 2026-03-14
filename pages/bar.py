from gi.repository import Adw, Gtk
from config import get, set as set_conf, write_conf

class BarPage(Adw.PreferencesPage):
    def __init__(self):
        super().__init__()
        self.set_icon_name("preferences-desktop-symbolic")

        appearence_group = Adw.PreferencesGroup(title="Menu Bar Appearance")

        margin_row = Adw.SpinRow(
            title="Margin",
            subtitle="Distance to tiled windows in pixels",
        )
        margin_row.set_range(0, 12)
        margin_row.get_adjustment().set_step_increment(1)
        margin_row.set_value(get("bar_margin", 2))
        margin_row.connect("notify::value", self.on_margin_changed)
        appearence_group.add(margin_row)

        self.add(appearence_group)

    def on_margin_changed(self, row, _):
        set_conf("bar_margin", int(row.get_value()))
        write_conf()
