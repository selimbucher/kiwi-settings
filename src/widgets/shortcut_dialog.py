from gi.repository import Adw, Gdk, GLib, Gtk

from utils import shortcuts


class ShortcutDialog(Adw.AlertDialog):
    """Captures a keybind for one of kiwi-shell's shortcuts.

    current: the keybind to change, or None to add one beside the action's
    others (siblings). on_chosen(response, shortcut): "set" with the keybind
    pressed, "remove" when current is to go, "reset" for the action's default.
    """

    def __init__(self, name, current, others, foreign_binds, on_chosen, siblings=()):
        if current is None and siblings:
            body = "Press another keybind for it."
        elif name == "launcher":
            body = "Press the new keybind, or tap a modifier on its own."
        else:
            body = "Press the new keybind."
        super().__init__(heading=shortcuts.TITLES[name], body=body)
        self._name = name
        self._others = others
        self._siblings = list(siblings)
        self._foreign = foreign_binds
        self._on_chosen = on_chosen
        self._captured = None
        self._tap = None
        self._toplevel = None

        self._label = Gtk.ShortcutLabel(accelerator=current.accelerator() if current else "", halign=Gtk.Align.CENTER)
        self._label.add_css_class("shortcut-capture")
        self._hint = Gtk.Label(wrap=True, justify=Gtk.Justification.CENTER, css_classes=["dim-label"])
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        # Wide enough for three buttons in a row: right at the edge of
        # fitting, AlertDialog flips them between a row and a stack on every
        # layout, without end.
        box.set_size_request(320, -1)
        box.append(self._label)
        box.append(self._hint)
        self.set_extra_child(box)

        self.add_response("cancel", "Cancel")
        default = shortcuts.Shortcut.parse(shortcuts.DEFAULT_SHORTCUTS[name])
        if current is not None and self._siblings:
            # one of several: the others stay
            self.add_response("remove", "Remove")
        elif current is not None and current != default:
            # an optional shortcut's default is none at all
            self.add_response("reset", "Reset to Default" if default else "Remove")
        self.add_response("set", "Add" if current is None and self._siblings else "Set")
        self.set_response_appearance("set", Adw.ResponseAppearance.SUGGESTED)
        self.set_response_enabled("set", False)
        self.set_default_response("cancel")
        self.set_close_response("cancel")
        self.connect("response", self._on_response)

        keys = Gtk.EventControllerKey(propagation_phase=Gtk.PropagationPhase.CAPTURE)
        keys.connect("key-pressed", self._on_key_pressed)
        keys.connect("key-released", self._on_key_released)
        self.add_controller(keys)

        self.connect("map", self._inhibit)
        self.connect("closed", self._restore)

    # Hyprland would otherwise act on the keys (Alt+Tab opening the switcher)
    # before they reach us. The inhibitor lives only as long as this surface,
    # so a crash can't leave the keyboard without shortcuts.
    def _inhibit(self, *_):
        surface = self.get_root().get_surface()
        if isinstance(surface, Gdk.Toplevel):
            self._toplevel = surface
            surface.inhibit_system_shortcuts(None)
            GLib.timeout_add(400, self._check_inhibited)

    def _check_inhibited(self):
        if self._toplevel and not self._toplevel.get_property("shortcuts-inhibited") and not self._captured:
            self._hint.set_label("Hyprland is still handling its own shortcuts, so some may not reach this dialog.")
        return GLib.SOURCE_REMOVE

    def _restore(self, *_):
        if self._toplevel:
            self._toplevel.restore_system_shortcuts()
            self._toplevel = None

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape and not state & Gtk.accelerator_get_default_mod_mask():
            self.close()
            return True
        tap = shortcuts.tap_for(keyval)
        if tap:
            self._tap = tap if self._tap is None else self._tap
            return True
        # the unshifted key: Shift+Tab arrives as ISO_Left_Tab
        display = controller.get_widget().get_display()
        ok, base, *_ = display.translate_key(keycode, Gdk.ModifierType(0), 0)
        key = Gdk.keyval_to_lower(base if ok else keyval)
        self._tap = None
        self._capture(shortcuts.from_key_event(key, state))
        return True

    def _on_key_released(self, controller, keyval, keycode, state):
        tap = shortcuts.tap_for(keyval)
        if tap and self._tap == tap:
            self._capture(tap)
        self._tap = None

    def _capture(self, shortcut):
        if shortcut is None:
            return
        self._label.set_accelerator(shortcut.accelerator())
        problem = shortcuts.problem(self._name, shortcut, self._others, self._siblings)
        if problem:
            self._captured = None
            self._hint.set_label(problem)
            self._hint.add_css_class("error")
            self._hint.remove_css_class("dim-label")
        else:
            self._captured = shortcut
            if shortcuts.taken_from_config(self._name, shortcut, self._foreign):
                self._hint.set_label("Your Hyprland config binds these keys too. Kiwi Shell turns that bind off while it runs.")
            else:
                self._hint.set_label("Tap" if shortcut.tap else "")
            self._hint.remove_css_class("error")
            self._hint.add_css_class("dim-label")
        self.set_response_enabled("set", self._captured is not None)

    def _on_response(self, _, response):
        if response == "set" and self._captured:
            self._on_chosen("set", self._captured)
        elif response in ("remove", "reset"):
            self._on_chosen(response, None)
