from gi.repository import Gtk, Adw, GObject, Gio, Gdk

class CenteringBox(Gtk.Box):
    def __init__(self, **kwargs):
        super().__init__(valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER, **kwargs)