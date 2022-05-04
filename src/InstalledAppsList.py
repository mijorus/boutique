from urllib import request
from gi.repository import Gtk, Adw, Gdk, GObject, Pango
from typing import Dict, List
import re

from .providers.providers_list import providers
from .models.AppListElement import AppListElement
from .models.Provider import Provider
from .components.FilterEntry import FilterEntry
from .components.AppListBoxItem import AppListBoxItem

class InstalledAppsList(Gtk.ScrolledWindow):
    __gsignals__ = {
      "selected-app": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object, )),
    }

    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.installed_apps_list_slot = Gtk.Box()
        self.installed_apps_list: Gtk.ListBox = None

        # Create the filter search bar
        self.filter_query: str = ''
        self.filter_entry = FilterEntry('Filter installed apps', capture=self, margin_bottom=20)
        self.filter_entry.connect('search-changed', self.trigger_filter_list)

        self.refresh_list()

        title_row = Gtk.Box(margin_bottom=5)
        title_row.append( Gtk.Label(label='Installed applications', css_classes=['title-2']) )
        
        self.main_box.append(self.filter_entry)
        self.main_box.append(title_row)
        self.main_box.append(self.installed_apps_list_slot)

        clamp = Adw.Clamp(child=self.main_box, maximum_size=600, margin_top=10, margin_bottom=20)
        self.set_child(clamp)


    def on_activated_row(self, listbox, row: Gtk.ListBoxRow):
        """Emit and event that changes the active page of the Stack in the parent widget"""
        self.emit('selected-app', row._app)

    def refresh_list(self):
        self.set_cursor(Gdk.Cursor.new_from_name('wait', None))
        if self.installed_apps_list:
            self.installed_apps_list_slot.remove(self.installed_apps_list)

        self.installed_apps_list= Gtk.ListBox(css_classes=["boxed-list"], show_separators=False)

        for p, provider in providers.items():
            installed: List[AppListElement] = provider.list_installed()

            for i in installed:
                list_row = AppListBoxItem(i, activatable=True, selectable=True, hexpand=True)
                self.installed_apps_list.append(list_row)

        self.installed_apps_list_slot.append(self.installed_apps_list)
        self.installed_apps_list.set_filter_func(self.filter_func)
        self.installed_apps_list.connect('row-activated', self.on_activated_row)
        self.set_cursor(Gdk.Cursor.new_from_name('default', None))

    def trigger_filter_list(self, widget):
        if not self.installed_apps_list:
            return

        self.filter_query = widget.get_text()
        self.installed_apps_list.invalidate_filter()

    def filter_func(self, row: Gtk.ListBoxRow):
        if not len(self.filter_query):
            row.set_visible(True)
            return True

        visible = self.filter_query.lower().replace(' ', '') in row._app.name.lower()
        row.set_visible(visible)

        return visible