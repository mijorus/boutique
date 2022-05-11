import threading
from urllib import request
from gi.repository import Gtk, Adw, Gdk, GObject, Pango
from typing import Dict, List, Optional
import re

from .providers.providers_list import providers
from .models.AppListElement import AppListElement, InstalledStatus
from .models.Provider import Provider
from .components.FilterEntry import FilterEntry
from .components.AppListBoxItem import AppListBoxItem
from .lib.utils import set_window_cursor

class InstalledAppsList(Gtk.ScrolledWindow):
    __gsignals__ = {
      "selected-app": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object, )),
    }

    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.installed_apps_list_slot = Gtk.Box()
        self.installed_apps_list: Optional[Gtk.ListBox] = None
        self.installed_apps_list_rows: List[Gtk.ListBox] = []

        # Create the filter search bar
        self.filter_query: str = ''
        self.filter_entry = FilterEntry('Filter installed applications', capture=self, margin_bottom=20)
        self.filter_entry.connect('search-changed', self.trigger_filter_list)

        self.refresh_list()

        self.updates_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, visible=False)
        self.updates_row_list: Optional[Gtk.ListBox] = None

        updates_title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, valign=Gtk.Align.CENTER, margin_bottom=5)
        updates_title_row.append( Gtk.Label(label='Available updates', css_classes=['title-4'], hexpand=True, halign=Gtk.Align.START) )
        
        self.update_all_btn =  Gtk.Button(label='Update all', css_classes=['suggested-action'], valign=Gtk.Align.CENTER) 
        self.update_all_btn.connect('clicked', self.on_update_all_btn_clicked)

        updates_title_row.append(self.update_all_btn)
        self.updates_row.append(updates_title_row)

        title_row = Gtk.Box(margin_bottom=5)
        title_row.append( Gtk.Label(label='Installed applications', css_classes=['title-2']) )
        
        self.main_box.append(self.filter_entry)
        self.main_box.append(self.updates_row)
        self.main_box.append(title_row)
        self.main_box.append(self.installed_apps_list_slot)

        clamp = Adw.Clamp(child=self.main_box, maximum_size=600, margin_top=20, margin_bottom=20)

        self.refresh_upgradable()
        self.set_child(clamp)

    def on_activated_row(self, listbox, row: Gtk.ListBoxRow):
        """Emit and event that changes the active page of the Stack in the parent widget"""
        self.emit('selected-app', row._app)

    def refresh_list(self):
        set_window_cursor('wait')
        if self.installed_apps_list:
            self.installed_apps_list_slot.remove(self.installed_apps_list)

        self.installed_apps_list= Gtk.ListBox(css_classes=["boxed-list"])
        self.installed_apps_list_rows = []

        for p, provider in providers.items():
            installed: List[AppListElement] = provider.list_installed()

            for i in installed:
                list_row = AppListBoxItem(i, activatable=True, selectable=True, hexpand=True)
                self.installed_apps_list_rows.append(list_row)
                self.installed_apps_list.append(list_row)

        self.installed_apps_list_slot.append(self.installed_apps_list)
        self.installed_apps_list.set_filter_func(self.filter_func)
        self.installed_apps_list.connect('row-activated', self.on_activated_row)
        set_window_cursor('default')

    def trigger_filter_list(self, widget):
        if not self.installed_apps_list:
            return

        self.filter_query = widget.get_text()
        self.installed_apps_list.invalidate_filter()

    def refresh_upgradable_list(self, only: Optional[str]=None):
        self.updates_row.set_visible(False)
        self.updates_row_list = Gtk.ListBox(css_classes=["boxed-list"], margin_bottom=25)
        self.updates_row_list.set_filter_func(self.filter_func)

        upgradable = 0
        for p, provider in providers.items():
            if only is not None and p != only:
                continue

            for upg in provider.list_updatable():
                for row in self.installed_apps_list_rows:
                    if row._app.id == upg.id:
                        upgradable += 1
                        row._app.set_installed_status(InstalledStatus.UPDATE_AVAILABLE)
                        app_list_item = AppListBoxItem(row._app, activatable=True, selectable=True, hexpand=True)
                        app_list_item.force_show = True
                        self.updates_row_list.append( app_list_item )
                        break

        if upgradable:
            self.updates_row.set_visible(True)

        self.updates_row.append(self.updates_row_list)
        self.updates_row_list.connect('row-activated', self.on_activated_row)
        self.installed_apps_list.invalidate_filter()

    def refresh_upgradable(self, only: Optional[str]=None):
        if self.updates_row_list:
            self.updates_row.remove(self.updates_row_list)

        thread = threading.Thread(target=self.refresh_upgradable_list, args=(only, ))
        thread.start()

    def filter_func(self, row: Gtk.ListBoxRow):
        if not getattr(row, 'force_show', False) and row._app.installed_status != InstalledStatus.INSTALLED:
            return False

        if not len(self.filter_query):
            row.set_visible(True)
            return True

        visible = self.filter_query.lower().replace(' ', '') in row._app.name.lower()
        row.set_visible(visible)

        return visible

    def after_update_all(self, result: bool, prov: str):
        if result:
            self.refresh_upgradable(only=prov)

    def on_update_all_btn_clicked(self, widget: Gtk.Button):
        if not self.updates_row_list:
            return

        self.updates_row_list.set_opacity(0.5)
        self.update_all_btn.set_label('Updating...')

        for p, provider in providers.items():
            provider.update_all(self.after_update_all)

        self.updates_row_list.set_opacity(1)
        self.update_all_btn.set_label('Update all')