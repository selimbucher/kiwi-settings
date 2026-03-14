import cairo
import math
from gi.repository import Gtk, Gdk
from config import get


class HueStrip(Gtk.Widget):
    S = 0.85
    L_MIN = 0.6
    L_MAX = 0.85

    def __init__(self, on_color_changed=None):
        super().__init__()
        self.on_color_changed = on_color_changed
        
        color = get("primary_color", "rgb(190,157,241)")
        h, l = self._css_to_hl(color)
        self.hue = h
        self.lightness = max(self.L_MIN, min(self.L_MAX, l))

        self.set_hexpand(True)
        self.set_size_request(-1, 80)

        self._canvas = Gtk.DrawingArea()
        self._canvas.set_hexpand(True)
        self._canvas.set_vexpand(True)
        self._canvas.set_draw_func(self._draw)
        self._cache: cairo.ImageSurface | None = None
        self._cache_size = (0, 0)
        self._canvas.set_parent(self)

        drag = Gtk.GestureDrag()
        drag.connect("drag-begin", self._on_drag_begin)
        drag.connect("drag-update", self._on_drag_update)
        self.add_controller(drag)

        click = Gtk.GestureClick()
        click.connect("pressed", self._on_click)
        self.add_controller(click)

    def _css_to_hl(self, color_str: str):
        """Parse any valid CSS color string and return (hue, lightness) in [0,1]."""
        rgba = Gdk.RGBA()
        if not rgba.parse(color_str):
            return 0.08, 0.72  # fallback: orange-ish
        r, g, b = rgba.red, rgba.green, rgba.blue
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        l = (max_c + min_c) / 2
        if max_c == min_c:
            return 0.0, l
        d = max_c - min_c
        if max_c == r:
            h = (g - b) / d % 6
        elif max_c == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        return h / 6, l

    def do_measure(self, orientation, for_size):
        return self._canvas.measure(orientation, for_size)

    def do_size_allocate(self, width, height, baseline):
        self._canvas.allocate(width, height, baseline, None)

    def _build_cache(self, width, height):
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)
        cr = cairo.Context(surface)
        for ix in range(width):
            h = ix / width
            for iy in range(height):
                l = self.L_MAX - (iy / height) * (self.L_MAX - self.L_MIN)
                r, g, b = self._hsl_to_rgb(h, self.S, l)
                cr.set_source_rgb(r, g, b)
                cr.rectangle(ix, iy, 1, 1)
                cr.fill()
        self._cache = surface
        self._cache_size = (width, height)

    def _draw(self, area, cr, width, height):
        if self._cache_size != (width, height):
            self._build_cache(width, height)

        r = 8
        cr.new_path()
        cr.arc(r,         r,          r, math.pi,         3 * math.pi / 2)
        cr.arc(width - r, r,          r, 3 * math.pi / 2, 2 * math.pi)
        cr.arc(width - r, height - r, r, 0,               math.pi / 2)
        cr.arc(r,         height - r, r, math.pi / 2,     math.pi)
        cr.close_path()
        cr.clip()

        cr.set_source_surface(self._cache, 0, 0)
        cr.paint()

        cx = self.hue * width
        cy = (self.L_MAX - self.lightness) / (self.L_MAX - self.L_MIN) * height
        cx = max(0, min(width, cx))
        cy = max(0, min(height, cy))

        cr.arc(cx, cy, 7, 0, 2 * math.pi)
        cr.set_source_rgb(1, 1, 1)
        cr.set_line_width(2)
        cr.stroke()

        cr.arc(cx, cy, 7, 0, 2 * math.pi)
        cr.set_source_rgba(0, 0, 0, 0.6)
        cr.set_line_width(1)
        cr.stroke()

    def _set_from_xy(self, x, y):
        width = self._canvas.get_width()
        height = self._canvas.get_height()
        if width == 0 or height == 0:
            return
        self.hue = max(0.0, min(1.0, x / width))
        self.lightness = max(self.L_MIN, min(self.L_MAX,
            self.L_MAX - (y / height) * (self.L_MAX - self.L_MIN)))
        self._canvas.queue_draw()
        if self.on_color_changed:
            self.on_color_changed(self.hue, self.lightness)

    def _on_drag_begin(self, gesture, x, y):
        self._set_from_xy(x, y)

    def _on_drag_update(self, gesture, dx, dy):
        ok, start_x, start_y = gesture.get_start_point()
        if not ok:
            return
        self._set_from_xy(start_x + dx, start_y + dy)

    def _on_click(self, gesture, n, x, y):
        self._set_from_xy(x, y)

    def _hsl_to_rgb(self, h, s, l):
        if s == 0:
            return l, l, l
        def hue2rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        return hue2rgb(p, q, h + 1/3), hue2rgb(p, q, h), hue2rgb(p, q, h - 1/3)