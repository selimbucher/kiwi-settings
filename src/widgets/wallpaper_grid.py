from gi.repository import Gtk

from utils.wallpaper import list_wallpapers, wallpaper_name
from widgets.thumbnail import Thumbnail


class WallpaperGrid(Gtk.FlowBox):
    """Every picture in the wallpaper folder; the current one is ringed."""

    def __init__(self, on_selected):
        super().__init__(
            homogeneous=True,
            min_children_per_line=2,
            max_children_per_line=4,
            row_spacing=12,
            column_spacing=12,
            selection_mode=Gtk.SelectionMode.NONE,
            valign=Gtk.Align.START,
        )
        self.add_css_class("wallpaper-grid")
        self._on_selected = on_selected
        self._tiles = {}
        self._paths = []

    def update(self, current):
        paths = list_wallpapers(current)
        if paths != self._paths:
            self._paths = paths
            self.remove_all()
            self._tiles.clear()
            for path in paths:
                self._tiles[path] = self._tile(path)
                self.append(self._tiles[path])
        for path, tile in self._tiles.items():
            if path == current:
                tile.add_css_class("current")
            else:
                tile.remove_css_class("current")

    def _tile(self, path):
        thumbnail = Thumbnail(152, 95, "wallpaper-image")
        thumbnail.set_path(path)
        button = Gtk.Button(child=thumbnail, tooltip_text=wallpaper_name(path), css_classes=["flat", "wallpaper-tile"])
        button.connect("clicked", lambda _: self._on_selected(path))
        return button
