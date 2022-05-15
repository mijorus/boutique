import threading
from gi.repository import Gtk, GObject, Adw, Gdk, Gio
from .models.AppListElement import AppListElement, InstalledStatus
from .models.Provider import Provider
from .providers import FlatpakProvider
from .providers.providers_list import providers
from .lib.utils import cleanhtml, key_in_dict, set_window_cursor

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

        title_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, spacing=2)
        self.title = Gtk.Label(label='', css_classes=['title-1'], hexpand=True, halign=Gtk.Align.START)
        self.version = Gtk.Label(label='', halign=Gtk.Align.START, css_classes=['dim-label'])
        self.app_id = Gtk.Label(label='', halign=Gtk.Align.START, selectable=True, css_classes=['dim-label'])

        title_col.append(self.title)
        title_col.append(self.app_id)
        title_col.append(self.version)

        self.primary_action_button = Gtk.Button(label='Install', valign=Gtk.Align.CENTER)
        self.secondary_action_button = Gtk.Button(label='', valign=Gtk.Align.CENTER, visible=False)
        self.primary_action_button.connect('clicked', self.on_primary_action_button_clicked)
        self.secondary_action_button.connect('clicked', self.on_secondary_action_button_clicked)

        self.details_row.append(self.icon_slot)
        self.details_row.append(title_col)
        self.details_row.append(self.secondary_action_button)
        self.details_row.append(self.primary_action_button)

        # 2nd row
        self.desc_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=20)
        self.description = Gtk.Label(label='', halign=Gtk.Align.START, wrap=True, selectable=True)
        
        self.desc_row.append(self.description)

        # 3rd row
        self.third_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.extra_data = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.third_row.append(self.extra_data)

        self.main_box.append(self.details_row)
        self.main_box.append(self.desc_row)
        self.main_box.append(self.third_row)


        clamp = Adw.Clamp(child=self.main_box, maximum_size=600, margin_top=10, margin_bottom=20)
        self.set_child(clamp)

    def set_app_list_element(self, el: AppListElement, load_from_network=False):
        self.app_list_element = el

        self.provider = providers[el.provider]

        icon = self.provider.get_icon(el, load_from_network=load_from_network)
        icon.set_pixel_size(45)
        
        self.details_row.remove(self.icon_slot)
        self.icon_slot = icon
        self.details_row.prepend(self.icon_slot)

        self.title.set_label(cleanhtml(el.name))
        self.update_installation_status(check_installed=True)

        version_label = key_in_dict(el.extra_data, 'version')
        self.version.set_markup( '' if not version_label else f'<small>{version_label}</small>' )
        self.app_id.set_markup( f'<small>{self.app_list_element.id}</small>' )
        
        self.description.set_label('')
        threading.Thread(target=self.load_description).start()

        self.third_row.remove(self.extra_data)
        self.extra_data = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.third_row.append(self.extra_data)
        self.provider.load_extra_data_in_appdetails(self.extra_data, self.app_list_element)

    def set_from_local_file(self, file: Gio.File):
        for p, provider in providers.items():
            if provider.can_install_file(file):
                pass # @todo

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

        elif self.app_list_element.installed_status == InstalledStatus.UPDATE_AVAILABLE:
            self.app_list_element.set_installed_status(InstalledStatus.UPDATING)
            self.update_installation_status()
            self.provider.update(
                self.app_list_element, 
                lambda result: self.update_installation_status()
            )

    def on_secondary_action_button_clicked(self, button: Gtk.Button):
        if self.app_list_element.installed_status == InstalledStatus.INSTALLED:
            set_window_cursor('wait')
            self.provider.run(self.app_list_element)
            set_window_cursor('default')

    def update_installation_status(self, check_installed=False):
        self.secondary_action_button.set_visible(False)

        if check_installed:
            self.app_list_element.installed_status = InstalledStatus.NOT_INSTALLED if not self.provider.is_installed(self.app_list_element) else InstalledStatus.INSTALLED

        if self.app_list_element.installed_status == InstalledStatus.INSTALLED:
            self.secondary_action_button.set_label('Open')
            self.secondary_action_button.set_visible(True)

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

        elif self.app_list_element.installed_status == InstalledStatus.UPDATE_AVAILABLE:
            self.primary_action_button.set_label('Update')
            self.primary_action_button.set_css_classes(['suggested-action'])

        elif self.app_list_element.installed_status == InstalledStatus.UPDATING:
            self.primary_action_button.set_label('Updating')
            self.primary_action_button.set_css_classes([])

    def load_description(self):
        spinner = Gtk.Spinner(spinning=True)
        self.desc_row.append(spinner)

        desc = self.provider.get_long_description(self.app_list_element) 
        self.desc_row.remove(spinner)

        self.description.set_markup(desc)

    def on_back(self, widget):
        self.emit('show_list', None)