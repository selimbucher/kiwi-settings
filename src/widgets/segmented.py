from gi.repository import Gtk


class Segmented(Gtk.Box):
    """Linked toggles, the way the shell's own theme tab offers a choice."""

    def __init__(self, options, on_change):
        super().__init__(spacing=0, halign=Gtk.Align.END, valign=Gtk.Align.CENTER, homogeneous=True)
        self.add_css_class("linked")
        self.add_css_class("segmented")
        self._on_change = on_change
        self._syncing = False
        self._buttons = {}

        group = None
        for value, label, icon_name in options:
            button = Gtk.ToggleButton()
            content = Gtk.Box(spacing=7, halign=Gtk.Align.CENTER)
            # a symbolic icon has no baseline to share with the label
            content.append(Gtk.Image(icon_name=icon_name, valign=Gtk.Align.CENTER))
            content.append(Gtk.Label(label=label))
            button.set_child(content)
            if group is None:
                group = button
            else:
                button.set_group(group)
            button.connect("toggled", self._on_toggled, value)
            self.append(button)
            self._buttons[value] = button

    def set_value(self, value):
        """select one without reporting the selection back"""
        button = self._buttons.get(value)
        if button is None or button.get_active():
            return
        self._syncing = True
        button.set_active(True)
        self._syncing = False

    def _on_toggled(self, button, value):
        if button.get_active() and not self._syncing:
            self._on_change(value)
