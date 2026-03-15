import gi
gi.require_version("Adw", "1")
from gi.repository import Adw
from window import KiwiSettingsWindow
import sys
import os

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
    elif len(sys.argv) == 3:
        command = sys.argv[1]
        if command == "color":
            image_path = sys.argv[2]
            if not os.path.isfile(image_path):
                print(f"ERROR: file not found: {image_path}", file=sys.stderr)
                sys.exit(1)
            from utils.colors import get_color
            color = get_color(image_path)
            if not color:
                print("ERROR: could not determine color", file=sys.stderr)
                sys.exit(1)
            print(color)
        else:
            print(f"ERROR: unknown command: {command}", file=sys.stderr)
            print("Usage: kiwi-settings [color <image_path>]", file=sys.stderr)
            sys.exit(1)
    else:
        print("ERROR: invalid arguments", file=sys.stderr)
        print("Usage: kiwi-settings [color <image_path>]", file=sys.stderr)
        sys.exit(1)