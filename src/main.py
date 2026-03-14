import gi
gi.require_version("Adw", "1")
from gi.repository import Adw
from window import KiwiSettingsWindow

class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.github.selimbucher.kiwi_settings")
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        win = KiwiSettingsWindow(application=app)
        win.present()

App().run()