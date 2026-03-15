import gi
gi.require_version("Adw", "1")
from gi.repository import Adw
from window import KiwiSettingsWindow
import sys
import os


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

class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.github.selimbucher.kiwi_settings")
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        win = KiwiSettingsWindow(application=app)
        win.present()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("--- Starting Kiwi Settings ---")
        App().run()
    elif len(sys.argv) in (2, 3):
        command = sys.argv[1]
        if command == "color":
            if len(sys.argv) != 3:
                print("Usage: kiwi-settings color <image_path>", file=sys.stderr)
                sys.exit(1)
            image_path = sys.argv[2]
            if not os.path.isfile(image_path):
                print(f"ERROR: file not found: {image_path}", file=sys.stderr)
                sys.exit(1)
            from utils.colors import get_color
            color = get_color(image_path)
            if not color:
                print("ERROR: could not determine color", file=sys.stderr)
                sys.exit(1)
            _print_color_output(color)
        elif command == "auto-color":
            image_path = sys.argv[2] if len(sys.argv) == 3 else None
            if not image_path:
                from utils.wallpaper import get_wallpaper_path
                image_path = get_wallpaper_path()
            if not image_path:
                print("ERROR: could not determine wallpaper path", file=sys.stderr)
                sys.exit(1)
            if not os.path.isfile(image_path):
                print(f"ERROR: file not found: {image_path}", file=sys.stderr)
                sys.exit(1)

            from utils.colors import get_color
            color = get_color(image_path)
            if not color:
                print("ERROR: could not determine color", file=sys.stderr)
                sys.exit(1)

            from config import set as set_conf, write_conf
            set_conf("auto_color", True)
            set_conf("primary_color", color)
            write_conf()
        else:
            print("Usage: kiwi-settings [color <image_path>] [auto-color [image_path]]", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: kiwi-settings [color <image_path>] [auto-color [image_path]]", file=sys.stderr)
        sys.exit(1)