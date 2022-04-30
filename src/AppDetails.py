import asyncio

from gi.repository import Gtk, GObject
from .models.AppListElement import AppListElement, InstalledStatus
from .providers import FlatpakProvider
from .lib.terminal import async_sh
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
        self.primary_action_button.connect('clicked', self.on_primary_action_button_clicked)

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
        self.update_installation_status()

    def on_primary_action_button_clicked(self, button: Gtk.Button):
        if self.app_list_element.installed_status == InstalledStatus.INSTALLED:
            self.app_list_element.set_installed_status(InstalledStatus.UNINSTALLING)
            self.update_installation_status()

            # await providers[self.app_list_element.provider].uninstall(self.app_list_element)
            # asyncio.run( )
            async_sh(
                f'flatpak remove com.bitstower.Markets/x86_64/stable --user -y --no-related',
                lambda output: self.update_installation_status()
            )

        elif self.app_list_element.installed_status == InstalledStatus.UNINSTALLING:
            pass

        elif self.app_list_element.installed_status == InstalledStatus.NOT_INSTALLED:
            providers[self.app_list_element.provider].install(self.app_list_element)
            self.update_installation_status()

    def update_installation_status(self):
        if self.app_list_element.installed_status == InstalledStatus.INSTALLED:
            self.primary_action_button.set_label('Uninstall')
            self.primary_action_button.set_css_classes(['destructive-action'])

        elif self.app_list_element.installed_status == InstalledStatus.UNINSTALLING:
            self.primary_action_button.set_label('Uninstalling...')
            self.primary_action_button.set_css_classes([])

        elif self.app_list_element.installed_status == InstalledStatus.NOT_INSTALLED:
            self.primary_action_button.set_label('Install')
            self.primary_action_button.set_css_classes(['suggested-action'])


    def on_back(self, widget):
        self.emit('show_list', None)
