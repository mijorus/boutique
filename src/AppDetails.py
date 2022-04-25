from gi.repository import Gtk
from .models.AppListElement import AppListElement

class AppDetails(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()

    def set_app_list_element(self, el: AppListElement):
        self.set_child( Gtk.Label(label=el.name) )