from concurrent.futures import ThreadPoolExecutor

from gi.repository import Gdk, GdkPixbuf, GLib, Gtk

_executor = ThreadPoolExecutor(max_workers=2)
_textures = {}


def _decode(path, width, height):
    # at thumbnail size: wallpapers are often 5-8K, 100 MB+ decoded in full
    _, image_width, image_height = GdkPixbuf.Pixbuf.get_file_info(path)
    if not image_width or not image_height:
        raise ValueError(f"not an image: {path}")
    factor = min(1, max(width / image_width, height / image_height))
    return GdkPixbuf.Pixbuf.new_from_file_at_scale(
        path, round(image_width * factor), round(image_height * factor), True
    )


class Thumbnail(Gtk.ScrolledWindow):
    """A picture cropped to a fixed size, decoded off the main loop.

    The scrolled window keeps Gtk.Picture from requesting the image's own size.
    Rounded corners only clip the picture with overflow hidden.
    """

    def __init__(self, width, height, css_class=None):
        super().__init__(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.NEVER,
            overflow=Gtk.Overflow.HIDDEN,
        )
        self.set_size_request(width, height)
        if css_class:
            self.add_css_class(css_class)
        self._width = width
        self._height = height
        self._key = None
        self._picture = Gtk.Picture(content_fit=Gtk.ContentFit.COVER)
        self.set_child(self._picture)

    def set_path(self, path):
        scale = 2
        key = (path, self._width * scale, self._height * scale)
        if key == self._key:
            return
        self._key = key
        if not path:
            self._picture.set_paintable(None)
            return
        if key in _textures:
            self._picture.set_paintable(_textures[key])
            return
        future = _executor.submit(_decode, *key)
        future.add_done_callback(lambda f: GLib.idle_add(self._loaded, key, f))

    def _loaded(self, key, future):
        try:
            texture = Gdk.Texture.new_for_pixbuf(future.result())
        except Exception as e:
            print(f"Failed to load thumbnail for {key[0]}: {e}")
            return GLib.SOURCE_REMOVE
        _textures[key] = texture
        if key == self._key:
            self._picture.set_paintable(texture)
        return GLib.SOURCE_REMOVE
