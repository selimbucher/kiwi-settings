from gi.repository import Adw, Gtk
from config import get, set as set_conf, write_conf


class DockPage(Adw.PreferencesPage):
    def __init__(self):
        super().__init__()
        self.set_icon_name("xapp-prefs-toolbar-symbolic")

        items_group = Adw.PreferencesGroup(title="Dock Items")

        home_row = Adw.SwitchRow(title="Home Folder")
        home_row.set_active(get("dock_home", True))
        home_row.connect("notify::active", lambda row, _: [set_conf("dock_home", row.get_active()), write_conf()])
        items_group.add(home_row)

        trash_row = Adw.SwitchRow(title="Trash")
        trash_row.set_active(get("dock_trash", True))
        trash_row.connect("notify::active", lambda row, _: [set_conf("dock_trash", row.get_active()), write_conf()])
        items_group.add(trash_row)

        self.add(items_group)

        appearance_group = Adw.PreferencesGroup(title="Dock Appearance")

        options = Gtk.StringList.new(["Default", "Auto-Hide", "Disabled"])
        mode_row = Adw.ComboRow(title="Mode", model=options)
        dock_values = ["default", "auto-hide", "disabled"]
        current_mode = get("dock", "default")
        selected_index = dock_values.index(current_mode) if current_mode in dock_values else 0
        mode_row.set_selected(selected_index)
        mode_row.connect("notify::selected", self.on_mode_changed)
        appearance_group.add(mode_row)

        margin_row = Adw.SpinRow(
            title="Margin",
            subtitle="Distance from tiled windows in pixels",
        )
        margin_row.set_range(0, 12)
        margin_row.get_adjustment().set_step_increment(1)
        margin_row.set_value(get("dock_margin", 2))
        margin_row.connect("notify::value", self.on_margin_changed)
        appearance_group.add(margin_row)

        icon_size_row = Adw.ActionRow(title="Icon Size")
        icon_size_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 42, 64, 1)
        icon_size_scale.set_value(get("dock_icon_size", 56))
        icon_size_scale.set_draw_value(True)
        icon_size_scale.set_hexpand(True)
        icon_size_scale.set_valign(Gtk.Align.CENTER)
        icon_size_scale.connect("value-changed", self.on_icon_size_changed)
        icon_size_row.add_suffix(icon_size_scale)
        appearance_group.add(icon_size_row)

        self.add(appearance_group)

    def on_mode_changed(self, row, _):
        set_conf("dock", row.get_selected_item().get_string().lower())
        write_conf()

    def on_margin_changed(self, row, _):
        set_conf("dock_margin", int(row.get_value()))
        write_conf()
    
    def on_icon_size_changed(self, scale):
        set_conf("dock_icon_size", int(scale.get_value()))
        write_conf()