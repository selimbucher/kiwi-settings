import math

import cairo
from gi.repository import Adw, Gdk, GdkPixbuf, Graphene, Gtk, Pango, PangoCairo

# The four styles really are one axis — how much of the desktop comes through
# the panels — so they read better as a track than as a dropdown. Order and
# values have to match kiwi-shell's THEME_STYLES. The last number is how much
# panel each style paints; the track fades along it, so the bar shows the axis.
STYLES = [
    ("granite", "Granite", 1.0),
    ("acrylic", "Acrylic", 0.85),
    ("tinted", "Tinted Glass", 0.42),
    ("clear", "Clear Glass", 0.1),
]

VALUES = [value for value, _, _ in STYLES]

BAR_HEIGHT = 28
KNOB_RADIUS = 10
# the knob rides inside the bar, so the end stops sit a knob in from its ends
STOP_INSET = KNOB_RADIUS + 4
# room around the bar for the focus ring, which is drawn outside it
TRACK_PAD = 3
LABEL_GAP = 8
LABEL_SPACING = 14
LABEL_SCALE = 0.85
CHECKER = 7


# a scale attribute rather than a smaller font description: GTK hands out the
# font in absolute units, where set_size() would quietly mean points again
QUIET = Pango.AttrList()
QUIET.insert(Pango.attr_scale_new(LABEL_SCALE))
LOUD = Pango.AttrList()
LOUD.insert(Pango.attr_scale_new(LABEL_SCALE))
LOUD.insert(Pango.attr_weight_new(Pango.Weight.BOLD))


def _mix(base, over, amount):
    """`over` blended into `base` by `amount`, as an (r, g, b) triple."""
    return tuple(a + (b - a) * amount for a, b in zip(base, over))


def _rounded(cr, x, y, width, height, radius):
    """Path a rounded rectangle; the caller fills, strokes or clips it."""
    cr.new_sub_path()
    cr.arc(x + width - radius, y + radius,          radius, -math.pi / 2, 0)
    cr.arc(x + width - radius, y + height - radius, radius, 0,            math.pi / 2)
    cr.arc(x + radius,         y + height - radius, radius, math.pi / 2,  math.pi)
    cr.arc(x + radius,         y + radius,          radius, math.pi,      3 * math.pi / 2)
    cr.close_path()


class GlassTrack(Gtk.Widget):
    """A bar fading from solid panel to bare glass, with a stop per style.

    The fade is the point: it shows what the setting does before the labels
    do. The wallpaper runs underneath it, so the see-through end shows the
    same thing the panels will.
    """

    def __init__(self, on_change):
        super().__init__()
        self._on_change = on_change
        self._index = 0
        self._layouts = None
        self._cache = None
        self._cache_key = None
        self._wallpaper = None

        self.set_hexpand(True)
        self.set_focusable(True)

        drag = Gtk.GestureDrag()
        drag.connect("drag-begin", self._on_drag_begin)
        drag.connect("drag-update", self._on_drag_update)
        self.add_controller(drag)

        click = Gtk.GestureClick()
        click.connect("pressed", self._on_click)
        self.add_controller(click)

        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self._on_key)
        self.add_controller(keys)

        self.connect("notify::has-focus", lambda *_: self.queue_draw())

    def set_wallpaper(self, path):
        """Redraw over a new desktop picture."""
        if path != self._wallpaper:
            self._wallpaper = path
            self._cache_key = None
            self.queue_draw()

    def set_index(self, index):
        """Move the knob without reporting the move back."""
        index = max(0, min(len(STYLES) - 1, index))
        if index != self._index:
            self._index = index
            self.queue_draw()

    def do_css_changed(self, change):
        # the font and every colour drawn here come out of the style
        self._layouts = None
        self._cache_key = None
        Gtk.Widget.do_css_changed(self, change)

    def do_measure(self, orientation, for_size):
        if orientation == Gtk.Orientation.HORIZONTAL:
            labels = sum(loud.get_pixel_size().width for _, loud in self._label_layouts())
            width = labels + LABEL_SPACING * (len(STYLES) - 1)
            return width, max(width, 420), -1, -1
        height = 2 * TRACK_PAD + BAR_HEIGHT + LABEL_GAP + self._label_height()
        return height, height, -1, -1

    def do_snapshot(self, snapshot):
        width = self.get_width()
        area = Graphene.Rect().init(0, 0, width, self.get_height())
        self._draw(snapshot.append_cairo(area), width)

    def _label_layouts(self):
        """One quiet and one emphasised layout per stop, in the widget's font."""
        if self._layouts is None:
            self._layouts = []
            for _, label, _ in STYLES:
                quiet = self.create_pango_layout(label)
                quiet.set_attributes(QUIET)
                loud = self.create_pango_layout(label)
                loud.set_attributes(LOUD)
                self._layouts.append((quiet, loud))
        return self._layouts

    def _label_height(self):
        return self._label_layouts()[0][1].get_pixel_size().height

    def _bar(self, width):
        """The bar's x and width, inset so the end labels stay in the widget."""
        layouts = self._label_layouts()
        # each end label is centred on a stop that already sits inset from the
        # bar, so only the half label reaching past that has to be given room
        left = round(max(0, layouts[0][1].get_pixel_size().width / 2 - STOP_INSET))
        right = round(max(0, layouts[-1][1].get_pixel_size().width / 2 - STOP_INSET))
        x = TRACK_PAD + left
        return x, max(2 * STOP_INSET, width - TRACK_PAD - right - x)

    def _stops(self, width):
        bar_x, bar_width = self._bar(width)
        first = bar_x + STOP_INSET
        last = bar_x + bar_width - STOP_INSET
        return [first + (last - first) * index / (len(STYLES) - 1) for index in range(len(STYLES))]

    def _paint_wallpaper(self, cr, width, scale):
        """The desktop picture as a band across the bar. False if unreadable."""
        if not self._wallpaper:
            return False
        try:
            _, image_width, image_height = GdkPixbuf.Pixbuf.get_file_info(self._wallpaper)
            if not image_width or not image_height:
                return False
            # scaled to the bar's width, then cropped to the middle band: a
            # wallpaper squashed to 28px tall is unrecognisable
            target = math.ceil(width * scale)
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                self._wallpaper, target, round(target * image_height / image_width), True
            )
        except Exception:
            return False
        band = pixbuf.get_height() / scale
        cr.save()
        cr.scale(1 / scale, 1 / scale)
        Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, round((BAR_HEIGHT - band) / 2 * scale))
        cr.paint()
        cr.restore()
        return True

    def _paint_checkers(self, cr, width, fg, dark):
        """The fallback ground, so the see-through end never reads as white."""
        base = (0.0, 0.0, 0.0) if dark else (1.0, 1.0, 1.0)
        squares = (_mix(base, fg, 0.03), _mix(base, fg, 0.14))
        for row in range(math.ceil(BAR_HEIGHT / CHECKER)):
            for column in range(math.ceil(width / CHECKER)):
                cr.set_source_rgb(*squares[(row + column) % 2])
                cr.rectangle(column * CHECKER, row * CHECKER, CHECKER, CHECKER)
                cr.fill()

    def _build_cache(self, width, fg, dark, scale):
        # at the monitor's own resolution, or the picture comes out smeared
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width * scale, BAR_HEIGHT * scale)
        surface.set_device_scale(scale, scale)
        cr = cairo.Context(surface)
        _rounded(cr, 0, 0, width, BAR_HEIGHT, BAR_HEIGHT / 2)
        cr.clip()

        base = (0.0, 0.0, 0.0) if dark else (1.0, 1.0, 1.0)
        if not self._paint_wallpaper(cr, width, scale):
            self._paint_checkers(cr, width, fg, dark)

        panel = _mix(base, fg, 0.34 if dark else 0.07)
        fade = cairo.LinearGradient(0, 0, width, 0)
        span = width - 2 * STOP_INSET
        for index, (_, _, coverage) in enumerate(STYLES):
            offset = (STOP_INSET + span * index / (len(STYLES) - 1)) / width
            fade.add_color_stop_rgba(min(1.0, max(0.0, offset)), *panel, coverage)
        cr.set_source(fade)
        cr.paint()
        return surface

    def _draw(self, cr, width):
        manager = Adw.StyleManager.get_default()
        dark = manager.get_dark()
        accent = manager.get_accent_color_rgba()
        color = self.get_color()
        fg = (color.red, color.green, color.blue)

        bar_x, bar_width = self._bar(width)
        scale = self.get_scale_factor()
        key = (bar_width, dark, fg, scale, self._wallpaper)
        if key != self._cache_key:
            self._cache = self._build_cache(bar_width, fg, dark, scale)
            self._cache_key = key

        cr.set_source_surface(self._cache, bar_x, TRACK_PAD)
        cr.paint()

        # the bar's own edge, so its shape survives the see-through end
        _rounded(cr, bar_x + 0.5, TRACK_PAD + 0.5, bar_width - 1, BAR_HEIGHT - 1, (BAR_HEIGHT - 1) / 2)
        cr.set_source_rgba(*fg, 0.16)
        cr.set_line_width(1)
        cr.stroke()

        middle = TRACK_PAD + BAR_HEIGHT / 2
        stops = self._stops(width)
        for index, x in enumerate(stops):
            if index != self._index:
                _rounded(cr, x - 1.5, middle - 5.5, 3, 11, 1.5)
                cr.set_source_rgba(*fg, 0.32)
                cr.fill()

        self._draw_knob(cr, stops[self._index], middle, accent, dark)

        if self.has_visible_focus():
            _rounded(cr, bar_x - 2, TRACK_PAD - 2, bar_width + 4, BAR_HEIGHT + 4, BAR_HEIGHT / 2 + 2)
            cr.set_source_rgba(accent.red, accent.green, accent.blue, 0.75)
            cr.set_line_width(2)
            cr.stroke()

        top = 2 * TRACK_PAD + BAR_HEIGHT + LABEL_GAP
        for index, x in enumerate(stops):
            quiet, loud = self._label_layouts()[index]
            layout = loud if index == self._index else quiet
            cr.move_to(round(x - layout.get_pixel_size().width / 2), top)
            cr.set_source_rgba(*fg, 1.0 if index == self._index else 0.55)
            PangoCairo.show_layout(cr, layout)

    def _draw_knob(self, cr, x, y, accent, dark):
        """White disc, accent ring: it has to read as picked on either end."""
        glow = cairo.RadialGradient(x, y + 1, KNOB_RADIUS - 2, x, y + 1, KNOB_RADIUS + 4)
        glow.add_color_stop_rgba(0, 0, 0, 0, 0.32 if dark else 0.20)
        glow.add_color_stop_rgba(1, 0, 0, 0, 0)
        cr.set_source(glow)
        cr.arc(x, y + 1, KNOB_RADIUS + 4, 0, 2 * math.pi)
        cr.fill()

        cr.arc(x, y, KNOB_RADIUS, 0, 2 * math.pi)
        cr.set_source_rgb(1, 1, 1)
        cr.fill()

        cr.arc(x, y, KNOB_RADIUS - 1, 0, 2 * math.pi)
        cr.set_source_rgb(accent.red, accent.green, accent.blue)
        cr.set_line_width(2)
        cr.stroke()

    def _pick(self, index):
        index = max(0, min(len(STYLES) - 1, index))
        if index != self._index:
            self._index = index
            self.queue_draw()
            self._on_change(index)

    def _stop_at(self, x):
        stops = self._stops(self.get_width())
        return min(range(len(stops)), key=lambda index: abs(stops[index] - x))

    def _on_drag_begin(self, gesture, x, y):
        self.grab_focus()
        self._pick(self._stop_at(x))

    def _on_drag_update(self, gesture, dx, dy):
        ok, start_x, _ = gesture.get_start_point()
        if ok:
            self._pick(self._stop_at(start_x + dx))

    def _on_click(self, gesture, n_press, x, y):
        self.grab_focus()
        self._pick(self._stop_at(x))

    def _on_key(self, controller, keyval, keycode, state):
        if keyval in (Gdk.KEY_Left, Gdk.KEY_Up, Gdk.KEY_KP_Left, Gdk.KEY_KP_Up):
            self._pick(self._index - 1)
        elif keyval in (Gdk.KEY_Right, Gdk.KEY_Down, Gdk.KEY_KP_Right, Gdk.KEY_KP_Down):
            self._pick(self._index + 1)
        elif keyval in (Gdk.KEY_Home, Gdk.KEY_KP_Home):
            self._pick(0)
        elif keyval in (Gdk.KEY_End, Gdk.KEY_KP_End):
            self._pick(len(STYLES) - 1)
        else:
            return Gdk.EVENT_PROPAGATE
        # the track sits in a list box that would otherwise move focus off it
        return Gdk.EVENT_STOP


class GlassSlider(Gtk.Box):
    """The panel styles on one axis, from solid to barely there."""

    def __init__(self, on_change):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("glass-slider")
        self._on_change = on_change

        title = Gtk.Label(label="Panel Style", xalign=0)
        title.add_css_class("glass-title")
        self.append(title)

        self._track = GlassTrack(lambda index: self._on_change(VALUES[index]))
        self.append(self._track)

    def set_value(self, style):
        """Move the track without reporting the move back."""
        self._track.set_index(VALUES.index(style) if style in VALUES else 0)

    def set_wallpaper(self, path):
        self._track.set_wallpaper(path)
