import gi
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk
from pages.appearance import AppearancePage
from pages.dock import DockPage
# from pages.bar import BarPage

class KiwiSettingsWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_default_size(900, 650)
        self.set_title("Kiwi Settings")

        # Sidebar list
        sidebar = Gtk.ListBox(css_classes=["navigation-sidebar"])
        sidebar.append(self._nav_row("preferences-desktop-appearance-symbolic", "Appearance"))
        sidebar.append(self._nav_row("dock-symbolic", "Dock"))
        sidebar.append(self._nav_row("panel-symbolic", "Bar"))
        sidebar.connect("row-selected", self._on_row_selected)

        # Pages
        self.pages = {
            "Appearance": AppearancePage(),
            "Dock": DockPage(),
            # "Bar": BarPage(),
        }

        self.content_view = Adw.ViewStack()
        for name, page in self.pages.items():
            self.content_view.add_named(page, name)

        # Sidebar header + scroll
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar_box.append(Adw.HeaderBar())
        scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, vexpand=True)
        scroll.set_child(sidebar)
        sidebar_box.append(scroll)

        # Content header
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.append(Adw.HeaderBar())
        content_box.append(self.content_view)

        # Split view
        split = Adw.NavigationSplitView()
        split.set_sidebar(Adw.NavigationPage.new(sidebar_box, "Settings"))
        split.set_content(Adw.NavigationPage.new(content_box, "Settings"))

        self.set_content(split)

        # Select first row
        sidebar.select_row(sidebar.get_row_at_index(0))

    def _nav_row(self, icon, label):
        box = Gtk.Box(spacing=12, margin_top=6, margin_bottom=6, margin_start=6)
        box.append(Gtk.Image(icon_name=icon))
        box.append(Gtk.Label(label=label))
        return Gtk.ListBoxRow(child=box)

    def _on_row_selected(self, listbox, row):
        if row:
            label = row.get_child().get_last_child().get_label()
            self.content_view.set_visible_child_name(label)