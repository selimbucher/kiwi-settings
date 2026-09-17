from gi.repository import Adw

from widgets.rows import combo_row, spin_row


class BarPage(Adw.PreferencesPage):
    def __init__(self):
        super().__init__()

        bar_group = Adw.PreferencesGroup(title="Status Bar")
        bar_group.add(spin_row("bar_margin", "Margin", 0, 12, "Gap to tiled windows, in pixels"))
        self.add(bar_group)

        indicator_group = Adw.PreferencesGroup(
            title="Volume and Brightness",
            description="The indicator shown while changing either",
        )
        indicator_group.add(
            combo_row("indicator_bar_position", "Position", [("bottom", "Bottom"), ("left", "Left")])
        )
        self.add(indicator_group)
