from gi.repository import Adw

from widgets.rows import combo_row, switch_row

# kiwi-shell's SEARCH_ENGINES (widgets/Launcher/providers.ts)
SEARCH_ENGINES = [
    ("duckduckgo", "DuckDuckGo"),
    ("google", "Google"),
    ("bing", "Bing"),
    ("brave", "Brave Search"),
    ("ecosia", "Ecosia"),
    ("startpage", "Startpage"),
    ("kagi", "Kagi"),
]


class DesktopPage(Adw.PreferencesPage):
    def __init__(self):
        super().__init__()

        desktop_group = Adw.PreferencesGroup(title="Desktop")
        desktop_group.add(
            switch_row("desktop_icons", "Desktop Icons", "Show the files in your Desktop folder behind all windows")
        )
        desktop_group.add(
            switch_row(
                "desktop_free_placement",
                "Free Placement",
                "Icons stay where you drop them instead of arranging themselves",
            )
        )
        self.add(desktop_group)

        monitor_group = Adw.PreferencesGroup(title="Multiple Monitors")
        monitor_group.add(
            combo_row(
                "popup_monitor",
                "Show Popups On",
                [("active", "Active Monitor"), ("primary", "Main Monitor")],
                subtitle="Where switchers, the launcher and notifications appear",
            )
        )
        self.add(monitor_group)

        spotlight_group = Adw.PreferencesGroup(title="Spotlight")
        spotlight_group.add(
            combo_row(
                "search_engine",
                "Web Search",
                SEARCH_ENGINES,
                subtitle="Where Spotlight's last row sends your search",
            )
        )
        self.add(spotlight_group)
