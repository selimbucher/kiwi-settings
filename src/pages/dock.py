from gi.repository import Adw, Gtk

from config import get, save
from widgets.rows import combo_row, spin_row, switch_row


class DockPage(Adw.PreferencesPage):
    def __init__(self):
        super().__init__()

        dock_group = Adw.PreferencesGroup(title="Dock")
        self.add(dock_group)

        dock_group.add(
            combo_row(
                "dock",
                "Visibility",
                [("default", "Always Shown"), ("auto-hide", "Auto-Hide"), ("disabled", "Off")],
            )
        )

        icon_size_row = Adw.ActionRow(title="Icon Size")
        icon_size_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 24, 64, 1)
        icon_size_scale.set_value(get("dock_icon_size"))
        icon_size_scale.set_draw_value(True)
        icon_size_scale.set_value_pos(Gtk.PositionType.LEFT)
        icon_size_scale.set_size_request(220, -1)
        icon_size_scale.set_valign(Gtk.Align.CENTER)
        icon_size_scale.connect("value-changed", lambda s: save("dock_icon_size", int(s.get_value())))
        icon_size_row.add_suffix(icon_size_scale)
        dock_group.add(icon_size_row)

        dock_group.add(
            switch_row("dock_full_width", "Full Width", "Stretch the dock across the whole screen, like a taskbar")
        )
        dock_group.add(spin_row("dock_margin", "Margin", 0, 12, "Gap to tiled windows, in pixels"))
        dock_group.add(switch_row("dock_arpeggio", "Sound Effects", "Play a note when hovering over icons"))

        items_group = Adw.PreferencesGroup(title="Items")
        items_group.add(switch_row("dock_home", "Home Folder"))
        items_group.add(switch_row("dock_trash", "Trash"))
        self.add(items_group)
