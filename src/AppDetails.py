import threading
import time
from typing import Optional
from .lib.utils import qq
from gi.repository import Gtk, GObject, Adw, Gdk, Gio
from .models.AppListElement import AppListElement, InstalledStatus
from .models.Provider import Provider
from .providers import FlatpakProvider
from .providers.providers_list import providers
from .lib.utils import cleanhtml, key_in_dict, set_window_cursor, get_application_window

class AppDetails(Gtk.ScrolledWindow):
    """The presentation screen for an application"""

    def __init__(self):
        super().__init__()
        self.app_list_element: AppListElement = None
        self.active_alt_source: Optional[AppListElement] = None
        self.alt_sources: list[AppListElement] = []

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=10, margin_bottom=10, margin_start=20, margin_end=20,)

        # 1st row
        self.details_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.icon_slot = Gtk.Box()

        title_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, spacing=2)
        self.title = Gtk.Label(label='', css_classes=['title-1'], hexpand=True, halign=Gtk.Align.START)
        self.version = Gtk.Label(label='', halign=Gtk.Align.START, css_classes=['dim-label'])
        self.app_id = Gtk.Label(label='', halign=Gtk.Align.START, selectable=True, css_classes=['dim-label'])

        for el in [self.title, self.app_id, self.version]:
            title_col.append(el)

        self.source_selector_hdlr = None
        self.source_selector = Gtk.ComboBoxText()
        self.source_selector_revealer = Gtk.Revealer(child=self.source_selector, transition_type=Gtk.RevealerTransitionType.CROSSFADE)

        self.primary_action_button = Gtk.Button(label='Install', valign=Gtk.Align.CENTER)
        self.secondary_action_button = Gtk.Button(label='', valign=Gtk.Align.CENTER, visible=False)

        self.primary_action_button.connect('clicked', self.on_primary_action_button_clicked)
        self.secondary_action_button.connect('clicked', self.on_secondary_action_button_clicked)

        for el in [self.icon_slot, title_col, self.secondary_action_button, self.primary_action_button]:
            self.details_row.append(el)

        # 2nd row
        self.desc_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=20)
        self.description = Gtk.Label(label='', halign=Gtk.Align.START, wrap=True, selectable=True)
        
        self.desc_row.append(self.description)

        # 3rd row
        self.third_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.extra_data = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.third_row.append(self.extra_data)

        for el in [self.details_row, self.desc_row, self.third_row]:
            self.main_box.append(el)

        clamp = Adw.Clamp(child=self.main_box, maximum_size=600, margin_top=10, margin_bottom=20)
        self.set_child(clamp)

    def set_app_list_element(self, el: AppListElement, load_icon_from_network=False, local_file=False, alt_sources: list[AppListElement]= []):
        self.app_list_element = el
        self.active_alt_source = None
        self.alt_sources = alt_sources
        self.local_file = local_file

        self.provider = providers[el.provider]
        is_installed, alt_list_element_installed = self.provider.is_installed(self.app_list_element, alt_sources)
        if is_installed and alt_list_element_installed:
            self.set_app_list_element(alt_list_element_installed, True)
            return

        self.load_list_element_details(el, load_icon_from_network)
        self.install_button_label_info = None

        self.provider.load_extra_data_in_appdetails(self.extra_data, self.app_list_element)

        ###
        self.install_button_label_info = None

        self.source_selector.remove_all()
        if self.source_selector_hdlr:
            self.source_selector.disconnect(self.source_selector_hdlr)

        if alt_sources:
            self.source_selector_revealer.set_reveal_child(True)
            active_source_id = None
            for i, alt_source in enumerate([self.app_list_element, *alt_sources]):
                source_id, source_title = self.provider.get_source_details(alt_source)
                self.source_selector.append(source_id, f'Install from: {source_title}')
                if i == 0: active_source_id = source_id

            self.source_selector.set_active_id( active_source_id )
            get_application_window().titlebar.set_title_widget(self.source_selector_revealer)
        else:
            self.source_selector_revealer.set_reveal_child(False)

        ###

        self.source_selector_hdlr = self.source_selector.connect('changed', self.on_source_selector_changed)
        self.update_installation_status(check_installed=True)

    def load_list_element_details(self, el: AppListElement, load_icon_from_network=False):
        icon = self.provider.get_icon(el, load_from_network=load_icon_from_network)
        
        self.details_row.remove(self.icon_slot)
        self.icon_slot = icon
        icon.set_pixel_size(45)
        self.details_row.prepend(self.icon_slot)

        self.title.set_label(cleanhtml(el.name))

        version_label = key_in_dict(el.extra_data, 'version')
        self.version.set_markup( '' if not version_label else f'<small>{version_label}</small>' )
        self.app_id.set_markup( f'<small>{self.app_list_element.id}</small>' )
        
        self.description.set_label('')
        threading.Thread(target=self.load_description).start()

        self.third_row.remove(self.extra_data)
        self.extra_data = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.third_row.append(self.extra_data)

    def set_from_local_file(self, file: Gio.File):
        for p, provider in providers.items():
            if provider.can_install_file(file):
                list_element = provider.create_list_element_from_file(file)
                self.set_app_list_element(list_element, True, True)
                return True

        return False

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
                self.active_alt_source or self.app_list_element,
                lambda result: self.update_installation_status()
            )

        elif self.app_list_element.installed_status == InstalledStatus.UPDATE_AVAILABLE:
            self.provider.uninstall(
                self.app_list_element, 
                lambda result: self.update_installation_status()
            )

    def on_secondary_action_button_clicked(self, button: Gtk.Button):
        if self.app_list_element.installed_status == InstalledStatus.INSTALLED:
            self.provider.run(self.app_list_element)
        elif self.app_list_element.installed_status == InstalledStatus.UPDATE_AVAILABLE:
            self.app_list_element.set_installed_status(InstalledStatus.UPDATING)
            self.update_installation_status()
            self.provider.update(
                self.app_list_element, 
                lambda result: self.update_installation_status()
            )

    def update_installation_status(self, check_installed=False):
        self.primary_action_button.set_css_classes([])
        self.secondary_action_button.set_visible(False)
        self.secondary_action_button.set_css_classes([])
        self.source_selector.set_visible(False)

        if check_installed:
            if self.provider.is_updatable(self.app_list_element.id):
                self.app_list_element.installed_status = InstalledStatus.UPDATE_AVAILABLE

            else:
                is_installed, _ = self.provider.is_installed(self.app_list_element)
                self.app_list_element.installed_status = qq(is_installed, InstalledStatus.INSTALLED, InstalledStatus.NOT_INSTALLED)

        if self.app_list_element.installed_status == InstalledStatus.INSTALLED:
            self.secondary_action_button.set_label('Open')
            self.secondary_action_button.set_visible(True)

            self.primary_action_button.set_label('Uninstall')
            self.primary_action_button.set_css_classes(['destructive-action'])

        elif self.app_list_element.installed_status == InstalledStatus.UNINSTALLING:
            self.primary_action_button.set_label('Uninstalling...')

        elif self.app_list_element.installed_status == InstalledStatus.INSTALLING:
            self.primary_action_button.set_label('Installing...')

        elif self.app_list_element.installed_status == InstalledStatus.NOT_INSTALLED:
            self.source_selector.set_visible(True)
            self.primary_action_button.set_css_classes(['suggested-action'])

            if self.install_button_label_info:
                self.primary_action_button.set_label(self.install_button_label_info)
            else:
                self.primary_action_button.set_label('Install')

        elif self.app_list_element.installed_status == InstalledStatus.UPDATE_AVAILABLE:
            self.secondary_action_button.set_label('Update')
            self.secondary_action_button.set_css_classes(['suggested-action'])
            self.secondary_action_button.set_visible(True)

            self.primary_action_button.set_label('Uninstall')
            self.primary_action_button.set_css_classes(['destructive-action'])

        elif self.app_list_element.installed_status == InstalledStatus.UPDATING:
            self.primary_action_button.set_label('Updating')

    def load_description(self):
        spinner = Gtk.Spinner(spinning=True)
        self.desc_row.append(spinner)

        desc = self.provider.get_long_description(self.app_list_element) 
        self.desc_row.remove(spinner)

        self.description.set_markup(desc)

    def on_source_selector_changed(self, widget):
        new_source_id = widget.get_active_id()

        if not new_source_id:
            return

        sources = [self.app_list_element, *self.alt_sources]
        sel_source = self.provider.get_selected_source(sources, new_source_id)
        sources.remove(sel_source)

        self.set_app_list_element(
            sel_source,
            load_icon_from_network=True,
            alt_sources=sources
        )