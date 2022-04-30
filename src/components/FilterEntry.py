from gi.repository import Gtk, Pango, GObject, Gio, GdkPixbuf, GLib, Adw
from typing import Dict, List


class FilterEntry(Gtk.SearchEntry):
    __gsignals__ = {
      "selected-app": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object, )),
    }

    def __init__(self, label, **kwargs):
        super().__init__(**kwargs)

        self.set_placeholder_text('Filter apps')