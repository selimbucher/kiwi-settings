from gi.repository import Gio, GLib


def ask(args, then=None):
    """A request to the running shell, over D-Bus as kiwictl's are; `then`
    gets its answer, or None where the shell isn't running."""
    def done(bus, result):
        try:
            answer = bus.call_finish(result).unpack()[0]
        except GLib.Error:
            answer = None
        if then:
            then(answer)

    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        bus.call("io.Astal.ags", "/io/Astal/Application", "io.Astal.Application", "Request",
                 GLib.Variant("(as)", (list(args),)), GLib.VariantType("(s)"), Gio.DBusCallFlags.NONE,
                 1000, None, done)
    except GLib.Error:
        if then:
            then(None)
