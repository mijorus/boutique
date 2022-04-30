from urllib import request
from gi.repository import Gtk, Adw, Gdk, GObject, Pango
from typing import Dict, List
import re

from .providers.providers_list import providers
from .models.AppListElement import AppListElement
from .models.Provider import Provider
from .components.FilterEntry import FilterEntry


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
        self.emit('selected-app', row._app)

    def refresh_list(self):
        if self.installed_apps_list:
            self.installed_apps_list_slot.remove(self.installed_apps_list)

        self.installed_apps_list= Gtk.ListBox(css_classes=["boxed-list"])

        for p, provider in providers.items():
            installed: List[AppListElement] = provider.list_installed()

            for i in installed:
                list_row = Gtk.ListBoxRow(activatable=True, selectable=True)
                list_row._app: AppListElement = i

                col = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

                image = provider.get_icon(i)
                image.set_pixel_size(45)
                col.append(image)

                app_details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER)
                app_details_box.append( Gtk.Label(label=f'<b>{i.name}</b>', halign=Gtk.Align.START, use_markup=True) )
                app_details_box.append( Gtk.Label(label=i.description, halign=Gtk.Align.START, lines=1, max_width_chars=100, ellipsize=Pango.EllipsizeMode.END) )
                
                col.append(app_details_box)
                list_row.set_child(col)

                self.installed_apps_list.append(list_row)

        self.installed_apps_list_slot.append(self.installed_apps_list)
        self.installed_apps_list.set_filter_func(self.filter_func)
        self.installed_apps_list.connect('row-activated', self.on_activated_row)

    def trigger_filter_list(self, widget):
        if not self.installed_apps_list:
            return

        self.filter_query = widget.get_text()
        self.installed_apps_list.invalidate_filter()

    def filter_func(self, row: Gtk.ListBoxRow):
        if not len(self.filter_query):
            return True

        return self.filter_query.lower().replace(' ', '') in row._app.name.lower()