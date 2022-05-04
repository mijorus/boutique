from gi.repository import Gtk, GObject
from .models.AppListElement import AppListElement, InstalledStatus
from .providers import FlatpakProvider
from .providers.providers_list import providers
from .lib.utils import cleanhtml, key_in_dict

class AppDetails(Gtk.ScrolledWindow):
    """The presentation screen for an application"""
    __gsignals__ = {
      "show_list": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object, )),
    }

    def __init__(self):
        super().__init__()
        self.app_list_element = None

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=10, margin_bottom=10, margin_start=20, margin_end=20,)

        # 1st row
        self.details_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.icon_slot = Gtk.Box()

        title_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True,)
        self.title = Gtk.Label(label='', css_classes=['title-1'], hexpand=True, halign=Gtk.Align.START)
        self.version = Gtk.Label(label='', halign=Gtk.Align.START)
        self.app_id = Gtk.Label(label='', halign=Gtk.Align.START)

        title_col.append(self.title)
        title_col.append(self.app_id)
        title_col.append(self.version)

        self.primary_action_button = Gtk.Button(label='Install', valign=Gtk.Align.CENTER)
        self.primary_action_button.connect('clicked', self.on_primary_action_button_clicked)

        self.details_row.append(self.icon_slot)
        self.details_row.append(title_col)
        self.details_row.append(self.primary_action_button)

        # 2nd row
        desc_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=20)
        self.description = Gtk.Label(label='', halign=Gtk.Align.START, wrap=True)
        
        desc_row.append(self.description)

        self.main_box.append(self.details_row)
        self.main_box.append(desc_row)
        self.set_child(self.main_box)

    def set_app_list_element(self, el: AppListElement, load_from_network=False):
        self.app_list_element = el

        self.provider = providers[el.provider]

        icon = self.provider.get_icon(el, load_from_network=load_from_network)
        icon.set_pixel_size(45)
        
        self.details_row.remove(self.icon_slot)
        self.icon_slot = icon
        self.details_row.prepend(self.icon_slot)

        self.title.set_label(cleanhtml(el.name))
        self.update_installation_status()

        version_label = key_in_dict(el.extra_data, 'version')
        self.version.set_label( '' if not version_label else version_label )
        self.app_id.set_label( self.app_list_element.id )
        
        self.description.set_markup( 
            self.provider.get_long_description(self.app_list_element),
        )

    def on_primary_action_button_clicked(self, button: Gtk.Button):
        if self.app_list_element.installed_status == InstalledStatus.INSTALLED:
            self.app_list_element.set_installed_status(InstalledStatus.UNINSTALLING)
            self.update_installation_status()

            self.provider.uninstall(
                self.app_list_element, 
                lambda result: self.update_installation_status()
            )

        elif self.app_list_element.installed_status == InstalledStatus.UNINSTALLING:
            pass

        elif self.app_list_element.installed_status == InstalledStatus.NOT_INSTALLED:
            self.app_list_element.set_installed_status(InstalledStatus.INSTALLING)
            self.update_installation_status()

            self.provider.install(
                self.app_list_element,
                lambda result: self.update_installation_status()
            )

    def update_installation_status(self):
        if self.app_list_element.installed_status == InstalledStatus.INSTALLED:
            self.primary_action_button.set_label('Uninstall')
            self.primary_action_button.set_css_classes(['destructive-action'])

        elif self.app_list_element.installed_status == InstalledStatus.UNINSTALLING:
            self.primary_action_button.set_label('Uninstalling...')
            self.primary_action_button.set_css_classes([])

        elif self.app_list_element.installed_status == InstalledStatus.INSTALLING:
            self.primary_action_button.set_label('Installing...')
            self.primary_action_button.set_css_classes([])

        elif self.app_list_element.installed_status == InstalledStatus.NOT_INSTALLED:
            self.primary_action_button.set_label('Install')
            self.primary_action_button.set_css_classes(['suggested-action'])

    def on_back(self, widget):
        self.emit('show_list', None)