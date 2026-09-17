import os
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, Gtk

USAGE = """Usage:
  kiwi-settings [page]                    open the settings, optionally on a page
  kiwi-settings color <image_path>        print the accent color for an image
  kiwi-settings auto-color [-o] [image]   set the accent color from an image (default: the wallpaper)"""


def _print_color_output(hex_color):
    if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        print(hex_color)
        return

    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
    except (ValueError, IndexError):
        print(hex_color)
        return

    # Use relative luminance to keep the label readable on light/dark colors.
    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    fg = "30" if luminance > 0.6 else "97"
    print(f"\x1b[48;2;{r};{g};{b}m\x1b[{fg}m {hex_color} \x1b[0m")


def _color_command(args):
    if len(args) != 1:
        print(USAGE, file=sys.stderr)
        return 1
    image_path = args[0]
    if not os.path.isfile(image_path):
        print(f"ERROR: file not found: {image_path}", file=sys.stderr)
        return 1
    from utils.colors import get_color

    color = get_color(image_path)
    if not color:
        print("ERROR: could not determine color", file=sys.stderr)
        return 1
    _print_color_output(color)
    return 0


def _auto_color_command(args):
    output_color = "-o" in args
    args = [arg for arg in args if arg != "-o"]
    if len(args) > 1:
        print(USAGE, file=sys.stderr)
        return 1

    image_path = args[0] if args else None
    if not image_path:
        from utils.wallpaper import get_wallpaper_path

        image_path = get_wallpaper_path()
    if not image_path:
        print("ERROR: could not determine wallpaper path", file=sys.stderr)
        return 1
    if not os.path.isfile(image_path):
        print(f"ERROR: file not found: {image_path}", file=sys.stderr)
        return 1

    from utils.colors import get_color

    color = get_color(image_path)
    if not color:
        print("ERROR: could not determine color", file=sys.stderr)
        return 1

    from config import set as set_conf, write_conf

    set_conf("auto_color", True)
    set_conf("primary_color", color)
    write_conf()

    if output_color:
        _print_color_output(color)
    return 0


class App(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="com.github.selimbucher.kiwi_settings",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )

    def do_startup(self):
        Adw.Application.do_startup(self)
        here = os.path.dirname(os.path.abspath(__file__))
        # icons no theme has, like the status bar's
        Gtk.IconTheme.get_for_display(Gdk.Display.get_default()).add_search_path(os.path.join(here, "icons"))
        css = Gtk.CssProvider()
        css.load_from_path(os.path.join(here, "style.css"))
        # above USER: the theme usually comes in through ~/.config/gtk-4.0/gtk.css,
        # and these classes exist only here
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_USER + 1
        )

    def do_command_line(self, command_line):
        # runs in the first instance, also for later `kiwi-settings <page>` calls
        from window import PAGE_IDS, KiwiSettingsWindow

        args = command_line.get_arguments()[1:]
        window = self.get_active_window() or KiwiSettingsWindow(application=self)
        if args and not window.show_page(args[0]):
            command_line.printerr(f"Unknown page: {args[0]} (one of {', '.join(PAGE_IDS)})\n")
        window.present()
        return 0


def main():
    args = sys.argv[1:]
    if args and args[0] in ("-h", "--help"):
        print(USAGE)
        return 0
    if args and args[0] == "color":
        return _color_command(args[1:])
    if args and args[0] == "auto-color":
        return _auto_color_command(args[1:])
    return App().run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
