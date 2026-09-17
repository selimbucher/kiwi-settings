from gi.repository import Adw, Gtk

from pages.appearance import AppearancePage
from pages.bar import BarPage
from pages.desktop import DesktopPage
from pages.dock import DockPage
from pages.keyboard import KeyboardPage
from pages.night_shift import NightShiftPage

# (id for `kiwi-settings <id>`, title, icon, page)
PAGES = [
    ("appearance", "Appearance", "preferences-desktop-appearance-symbolic", AppearancePage),
    ("desktop", "Desktop", "user-desktop-symbolic", DesktopPage),
    ("dock", "Dock", "xapp-prefs-toolbar-symbolic", DockPage),
    ("bar", "Status Bar", "panel-top-symbolic", BarPage),
    ("night-shift", "Night Shift", "night-light-symbolic", NightShiftPage),
    ("keyboard", "Keyboard", "input-keyboard-symbolic", KeyboardPage),
]
PAGE_IDS = [page_id for page_id, *_ in PAGES]


class KiwiSettingsWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(title="Kiwi Settings", default_width=900, default_height=650, **kwargs)

        self._stack = Adw.ViewStack()
        self._titles = {}
        self._rows = {}
        self._sidebar = Gtk.ListBox(css_classes=["navigation-sidebar"])
        for page_id, title, icon, page_class in PAGES:
            page = page_class()
            self._stack.add_named(page, page_id)
            self._titles[page_id] = title
            if page_id == "appearance":
                self._appearance = page
            if page_id == "keyboard":
                self._keyboard = page

            row_box = Gtk.Box(spacing=12, margin_top=6, margin_bottom=6, margin_start=6)
            row_box.append(Gtk.Image(icon_name=icon))
            row_box.append(Gtk.Label(label=title))
            row = Gtk.ListBoxRow(child=row_box, name=page_id)
            self._rows[page_id] = row
            self._sidebar.append(row)
        self._sidebar.connect("row-activated", lambda _, row: self.show_page(row.get_name()))

        sidebar_view = Adw.ToolbarView(
            content=Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, child=self._sidebar)
        )
        sidebar_view.add_top_bar(Adw.HeaderBar())

        self._content_title = Adw.WindowTitle()
        content_header = Adw.HeaderBar(title_widget=self._content_title)
        content_view = Adw.ToolbarView(content=self._stack)
        content_view.add_top_bar(content_header)

        self._content_page = Adw.NavigationPage(child=content_view, title="Kiwi Settings")
        self._split = Adw.NavigationSplitView(
            sidebar=Adw.NavigationPage(child=sidebar_view, title="Settings"),
            content=self._content_page,
        )
        self.set_content(self._split)

        narrow = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 560sp"))
        narrow.add_setter(self._split, "collapsed", True)
        self.add_breakpoint(narrow)

        self.connect("notify::is-active", self._on_active_changed)

        self.show_page("appearance")

    def _on_active_changed(self, window, _):
        # kiwi-shell or a terminal may have changed things meanwhile
        if window.is_active():
            self._appearance.refresh()
            self._keyboard.refresh()

    def show_page(self, page_id):
        if page_id not in self._rows:
            return False
        self._sidebar.select_row(self._rows[page_id])
        self._stack.set_visible_child_name(page_id)
        self._content_title.set_title(self._titles[page_id])
        self._content_page.set_title(self._titles[page_id])
        self._split.set_show_content(True)
        # otherwise the first entry on the page takes focus and shows selected
        self._rows[page_id].grab_focus()
        return True
