from gi.repository import Gtk, GObject
from .models.AppListElement import AppListElement
from .providers import FlatpakProvider
from .providers.providers_list import providers

class AppDetails(Gtk.ScrolledWindow):
    """The presentation screen for an application"""
    __gsignals__ = {
      "show_list": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object, )),
    }

    def __init__(self):
        super().__init__()
        self.app_list_element = None

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=10, margin_bottom=10)

        # 1st row
        self.details_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin_start=20, margin_end=20, spacing=10)
        self.icon_slot = Gtk.Box()
        self.title = Gtk.Label(label='', css_classes=['title-1'], hexpand=True, halign=Gtk.Align.START)

        self.primary_action_button = Gtk.Button(label='Install', valign=Gtk.Align.CENTER)
        self.primary_action_button.connect('clicked', self.on_primary_action_button_cliecked)

        self.details_row.append(self.icon_slot)
        self.details_row.append(self.title)
        self.details_row.append(self.primary_action_button)

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
        self.primary_action_button.set_label('Uninstall')
        self.primary_action_button.set_css_classes(['.destructive-action'])

    def on_primary_action_button_cliecked(self, button: Gtk.Button):
        pass

    def on_back(self, widget):
        self.emit('show_list', None)
