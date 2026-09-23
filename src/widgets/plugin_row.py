"""The row that says whether kiwi-shell's Hyprland plugin is there, and helps set it up.

hyprpm builds the plugin against the running Hyprland, and installing
Hyprland's headers is a step that asks for your password — which a settings
window has no business collecting. So the parts that need it are handed over
as commands to run, with a button to copy them, and only what runs as you
(reloading) is run from here.
"""

from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from utils import plugin

WORDING = {
    "active": (
        "Active",
        "The dock follows dragged windows and the switchers show them live. "
        "hyprpm rebuilds it after a Hyprland update.",
    ),
    "shipped": (
        "Active",
        "The dock follows dragged windows and the switchers show them live. "
        "It comes with kiwi-shell on this system.",
    ),
    "installed": (
        "Built, but not loaded",
        "Load it, and add `exec-once = hyprpm reload -n` to your Hyprland config.",
    ),
    "missing": (
        "Not installed",
        "Without it the dock only sees a window once you drop it, and the switchers "
        "capture their previews instead of showing them live.",
    ),
    "unavailable": (
        "Not installed",
        "It is built by hyprpm, which comes with Hyprland; on some systems kiwi-shell's "
        "own package ships it.",
    ),
}

# label, commands, and whether they can run as you
ACTIONS = {
    "active": ("Update…", plugin.update_commands, False),
    "installed": ("Load", plugin.reload_commands, True),
    "missing": ("Set Up…", plugin.setup_commands, False),
}


class PluginRow(Adw.ActionRow):
    def __init__(self):
        super().__init__(title="Compositor Plugin")
        self._button = Gtk.Button(valign=Gtk.Align.CENTER)
        self._button.connect("clicked", self._on_clicked)
        self.add_suffix(self._button)
        self.refresh()

    def refresh(self):
        state = plugin.state()
        title, subtitle = WORDING[state]
        self.set_subtitle(f"{title}. {subtitle}")

        label, commands, runnable = ACTIONS.get(state, (None, None, False))
        self._commands = commands
        self._runnable = runnable
        self._button.set_visible(label is not None)
        if label:
            self._button.set_label(label)
            self._button.set_css_classes(["suggested-action"] if state == "missing" else [])

    def _on_clicked(self, _button):
        commands = self._commands()
        dialog = RunDialog(commands, self.refresh) if self._runnable else CopyDialog(commands)
        dialog.present(self.get_root())


def _as_text(commands):
    return "\n".join(" ".join(command) for command in commands)


class CopyDialog(Adw.AlertDialog):
    """The commands to run, for the steps that ask for a password."""

    def __init__(self, commands):
        super().__init__(
            heading="Run these in a terminal",
            body="Building the plugin installs Hyprland's headers, which asks for your "
            "password. Afterwards it is rebuilt with `hyprpm update` after every "
            "Hyprland update.",
        )
        self._text = _as_text(commands)

        # selectable, but not focusable: a selectable label takes focus when
        # the dialog opens and shows everything highlighted
        label = Gtk.Label(label=self._text, xalign=0, selectable=True, focusable=False, wrap=True)
        label.add_css_class("monospace")
        frame = Gtk.Frame(child=label, margin_top=6)
        frame.add_css_class("view")
        self.set_extra_child(frame)

        self.add_response("close", "Close")
        self.add_response("copy", "Copy")
        self.set_response_appearance("copy", Adw.ResponseAppearance.SUGGESTED)
        self.set_default_response("copy")
        self.connect("response", self._on_response)

    def _on_response(self, _dialog, response):
        if response == "copy":
            Gdk.Display.get_default().get_clipboard().set(self._text)


class RunDialog(Adw.Dialog):
    """Runs commands one after another, showing what they print."""

    def __init__(self, commands, on_done):
        super().__init__(title="Compositor Plugin", content_width=620, content_height=440)
        self._commands = list(commands)
        self._on_done = on_done

        self._output = Gtk.TextView(
            editable=False, monospace=True, cursor_visible=False, left_margin=12, right_margin=12
        )
        scroller = Gtk.ScrolledWindow(child=self._output, vexpand=True)

        self._spinner = Adw.Spinner(width_request=18, height_request=18)
        self._close = Gtk.Button(label="Close", visible=False)
        self._close.connect("clicked", lambda _: self.close())

        header = Adw.HeaderBar(show_end_title_buttons=False)
        header.pack_start(self._spinner)
        header.pack_end(self._close)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(header)
        box.append(scroller)
        self.set_child(box)

        self._next()

    def _write(self, text):
        buffer = self._output.get_buffer()
        buffer.insert(buffer.get_end_iter(), text)
        self._output.scroll_to_iter(buffer.get_end_iter(), 0, False, 0, 0)

    def _next(self):
        if not self._commands:
            self._spinner.set_visible(False)
            self._close.set_visible(True)
            self._on_done()
            return

        command = self._commands.pop(0)
        self._write(f"$ {' '.join(command)}\n")
        try:
            process = Gio.Subprocess.new(
                command, Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE
            )
        except GLib.Error as error:
            self._write(f"{error.message}\n")
            self._commands.clear()
            self._next()
            return

        self._read(Gio.DataInputStream.new(process.get_stdout_pipe()), process)

    def _read(self, stream, process):
        def on_line(source, result):
            try:
                line, _ = source.read_line_finish_utf8(result)
            except GLib.Error:
                line = None
            if line is None:
                process.wait_check_async(None, on_finished)
                return
            self._write(f"{line}\n")
            source.read_line_async(GLib.PRIORITY_DEFAULT, None, on_line)

        def on_finished(source, result):
            try:
                source.wait_check_finish(result)
            except GLib.Error as error:
                self._write(f"{error.message}\n")
                self._commands.clear()
            self._next()

        stream.read_line_async(GLib.PRIORITY_DEFAULT, None, on_line)
