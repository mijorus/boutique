from gi.repository import Gtk, Adw, GObject, Gio, Gdk

class CenteringBox(Gtk.Box):
    def __init__(self, **kwargs):
        super().__init__(valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER, **kwargs)

class LabelStart(Gtk.Label):
    def __init__(self, **kwargs):
        super().__init__(halign=Gtk.Align.START, **kwargs)

class LabelCenter(Gtk.Label):
    def __init__(self, **kwargs):
        super().__init__(halign=Gtk.Align.CENTER, **kwargs)