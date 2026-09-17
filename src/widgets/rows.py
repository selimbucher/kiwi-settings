from gi.repository import Adw, Gtk

from config import get, save


def switch_row(key, title, subtitle=None):
    row = Adw.SwitchRow(title=title, subtitle=subtitle or "")
    row.set_active(get(key))
    row.connect("notify::active", lambda r, _: save(key, r.get_active()))
    return row


def combo_row(key, title, options, subtitle=None):
    """options: [(config value, label), ...]"""
    values = [value for value, _ in options]
    row = Adw.ComboRow(
        title=title,
        subtitle=subtitle or "",
        model=Gtk.StringList.new([label for _, label in options]),
    )
    current = get(key)
    row.set_selected(values.index(current) if current in values else 0)
    row.connect("notify::selected", lambda r, _: save(key, values[r.get_selected()]))
    return row


def spin_row(key, title, lower, upper, subtitle=None):
    row = Adw.SpinRow.new_with_range(lower, upper, 1)
    row.set_title(title)
    row.set_subtitle(subtitle or "")
    row.set_value(get(key))
    row.connect("notify::value", lambda r, _: save(key, int(r.get_value())))
    return row
