import threading
import asyncio
from urllib import request
from gi.repository import Gtk, Adw, Gdk, GObject, Pango, GLib
from typing import Dict, List, Optional
import re

from .providers.providers_list import providers
from .models.AppListElement import AppListElement, InstalledStatus
from .models.Provider import Provider
from .models.Models import AppUpdateElement
from .components.FilterEntry import FilterEntry
from .components.CustomComponents import NoAppsFoundRow
from .components.AppListBoxItem import AppListBoxItem
from .lib.utils import set_window_cursor, key_in_dict, log


class UpdatesList(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.busy = False
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.no_apps_found_row = NoAppsFoundRow(visible=False)

        messages_row = Gtk.ListBox(css_classes=["boxed-list"], margin_bottom=25)
        messages_row.append(Adw.ActionRow(title='Messages', subtitle='reported'))

        # updates row
        self.updates_fetched = False
        self.updates_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, visible=True)

        # the list box containing all the updatable apps
        self.updates_row_list_items = []
        self.updates_row_list = Gtk.ListBox(css_classes=["boxed-list"], margin_bottom=25)

        
        self.updates_title_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        
        self.updates_title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin_bottom=10, spacing=5)
        self.updates_title_container.append(self.updates_title_row)
        
        self.updates_row_list_spinner = Gtk.Spinner(spinning=True, margin_start=5, visible=False)
        self.updates_title_container.append(self.updates_row_list_spinner)

        self.updates_title_label = Gtk.Label(label='', css_classes=['title-4'], hexpand=True, halign=Gtk.Align.START)
        self.updates_title_row.append(self.updates_title_label)

        self.update_all_btn = Gtk.Button(label='Update all', css_classes=['suggested-action'], valign=Gtk.Align.CENTER, visible=False)
        self.update_all_btn.connect('clicked', self.on_update_all_btn_clicked)

        self.updates_title_row.append(self.update_all_btn)
        self.updates_row.append(self.updates_title_container)
        self.updates_row.append(self.updates_row_list)

        self.main_box.append(messages_row)
        self.main_box.append(self.updates_row)

        clamp = Adw.Clamp(child=self.main_box, maximum_size=600, margin_top=20, margin_bottom=20)
        self.set_child(clamp)

    def on_show(self, only_provider: Optional[str] = None):
        if self.busy:
            return

        self.busy = True

        for widget in self.updates_row_list_items:
            self.updates_row_list.remove(widget)

        self.toggle_updates_title_label_state('Searching for updates...', True)
        self.updates_row_list_spinner.set_visible(True)
        self.updates_row_list.set_css_classes(["boxed-list"])

        threading.Thread(target=self.async_load_upgradable, daemon=True).start()

    # Runs the background task to check for app updates
    def async_load_upgradable(self, only_provider: Optional[str] = None):
        updatable_elements = []

        for p, provider in providers.items():
            apps = provider.list_installed()

            for upg in provider.list_updatables():
                for a in apps:
                    if (a.id == upg.id):
                        upg.extra_data['app_list_element'] = a

                        if a.extra_data and upg.to_version:
                            if ('version' in a.extra_data) and (a.extra_data['version'] != upg.to_version):
                                upg.to_version = a.extra_data['version'] + ' > ' + upg.to_version

                        updatable_elements.append(upg)
                        break

        GLib.idle_add(self.render_updatables, updatable_elements)

    def render_updatables(self, updatable_elements: List[AppUpdateElement]):
        upgradable_count = 0

        for upg in updatable_elements:
            update_is_an_app = False

            list_element = upg.extra_data['app_list_element']

            app_list_item = AppListBoxItem(list_element, activatable=False, selectable=False, hexpand=True)
            if  upg.to_version:
                app_list_item.set_update_version(upg.to_version)
            
            GLib.idle_add(app_list_item.load_icon)

            self.updates_row_list.append(app_list_item)
            self.updates_row_list_items.append(app_list_item)

        self.updates_fetched = True
        self.updates_row_list_spinner.set_visible(False)

        if updatable_elements:
            self.toggle_updates_title_label_state('Available updates', False)
        else:
            self.toggle_updates_title_label_state('Everything is up to date!', True)

        self.busy = False

    def toggle_updates_title_label_state(self, label: str, show_as_title: bool):
        self.updates_title_label.set_label(label)

        if show_as_title:
            self.update_all_btn.set_visible(False)
            self.updates_title_label.set_css_classes(['title-3'])

            self.updates_title_container.set_vexpand(True)
            self.updates_title_container.set_halign(Gtk.Align.CENTER)
            self.updates_title_container.set_valign(Gtk.Align.CENTER)

            self.updates_row_list.set_visible(False)
        else:
            self.updates_row_list.set_visible(True)

            self.updates_title_label.set_css_classes(['title-4'])

            self.updates_title_container.set_vexpand(False)
            self.updates_title_container.set_halign(Gtk.Align.FILL)
            self.updates_title_container.set_halign(Gtk.Align.FILL)
            self.updates_title_container.set_valign(Gtk.Align.START)

            self.update_all_btn.set_visible(True)

    def after_update_all(self, result: bool, prov: str):
        if result and (not self.update_all_btn.has_css_class('destructive-action')):
            if self.updates_row_list and prov == [*providers.keys()][-1]:
                self.updates_row_list.set_opacity(1)
                self.update_all_btn.set_sensitive(True)
                self.update_all_btn.set_label('Update all')

        else:
            self.update_all_btn.set_label('Error')
            self.update_all_btn.set_css_classes(['destructive-action'])

        self.refresh_upgradable(only_provider=prov)

    def on_update_all_btn_clicked(self, widget: Gtk.Button):
        if not self.updates_row_list:
            return

        self.updates_row_list.set_opacity(0.5)
        self.update_all_btn.set_sensitive(False)
        self.update_all_btn.set_label('Updating...')

        for p, provider in providers.items():
            provider.update_all(self.after_update_all)
