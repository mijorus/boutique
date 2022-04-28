from gi.repository import Gtk, GObject
from .models.AppListElement import AppListElement
from .providers import FlatpakProvider
from .providers.providers_list import providers

class AppDetails(Gtk.ScrolledWindow):
    __gsignals__ = {
      "show_list": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object, )),
    }

    def __init__(self):
        super().__init__()
        self.app_list_element = None

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.back_arrow = Gtk.Button(label='back',)
        self.back_arrow.connect('clicked', self.on_back)
        self.main_box.append(self.back_arrow)   

        # 1st row
        self.details_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.icon_slot = Gtk.Box()
        self.title = Gtk.Label(label='', css_classes=['title-3'])

        self.details_row.append(self.icon_slot)
        self.details_row.append(self.title)

        self.main_box.append(self.details_row)
        self.set_child(self.main_box)

    def set_app_list_element(self, el: AppListElement):
        self.app_list_element = el

        provider = providers[el.provider]

        icon = provider.get_icon(el)
        icon.set_pixel_size(45)
        
        self.details_row.remove(self.icon_slot)
        self.icon_slot = icon
        self.details_row.prepend(self.icon_slot)

        self.title.set_label(el.name)

    def on_back(self, widget):
        self.emit('show_list', None)
