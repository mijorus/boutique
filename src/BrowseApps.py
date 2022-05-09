import time
import threading
from typing import List, Dict
from .lib import flatpak, utils
from .models.AppListElement import AppListElement
from .models.Provider import Provider
from .providers.providers_list import providers
from .components.AppListBoxItem import AppListBoxItem

from gi.repository import Gtk, Adw, GObject, Gio, Gdk

class BrowseApps(Gtk.ScrolledWindow):
    __gsignals__ = {
      "selected-app": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object, )),
    }

    def __init__(self):
        super().__init__()

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=20, margin_bottom=20)

        self.search_entry = Gtk.SearchEntry()
        self.search_results: Gtk.ListBox = None

        self.search_entry.props.placeholder_text = 'Press "Enter" to search'
        self.search_entry.connect('activate', self.on_search_entry_activated)

        self.main_box.append(self.search_entry)

        self.search_results: Gtk.ListBox|None = None
        self.search_results_slot = Gtk.Box()
        self.main_box.append(self.search_results_slot)

        clamp = Adw.Clamp(child=self.main_box, maximum_size=600, margin_top=10, margin_bottom=20)
        self.set_child(clamp)

    def on_activated_row(self, listbox: Gtk.ListBox, row: Gtk.ListBoxRow):
        """Emit and event that changes the active page of the Stack in the parent widget"""
        self.emit('selected-app', row._app)

    def on_search_entry_activated(self, widget: Gtk.SearchEntry):
        query = widget.get_text()

        if self.search_results:
            self.search_results_slot.remove(self.search_results)

        if len(query) < 3:
            return

        widget.set_text('')
        self.search_results = Gtk.ListBox(hexpand=True, margin_top=10)

        # Perform search across all the providers
        Gio.Application.get_default().mark_busy()

        results: List[AppListElement] = []
        for p, provider in providers.items():
            thread = threading.Thread(target=self.populate_search, args=(query, provider, ), daemon=True)
            thread.start()

        self.search_results_slot.append(self.search_results)
        self.search_results.connect('row-activated', self.on_activated_row)

    def populate_search(self, query: str, provider: Provider):
        """Async function to populate the listbox without affecting the main thread"""
        self.search_results.set_css_classes(['boxed-list'])
        spinner = Gtk.ListBoxRow(child=Gtk.Spinner(spinning=True, margin_top=5, margin_bottom=5))
        self.search_results.append(spinner)

        utils.set_window_cursor('wait')
        result: List[AppListElement] = provider.search(query)

        self.search_results.remove(spinner)

        if not result:
            list_row = Gtk.Label(
                label='No apps found',
                margin_top=20,
                margin_bottom=20,
            )

            self.search_results.append(list_row)

        else:
            for app in result:
                list_row = AppListBoxItem(app, load_icon_from_network=True, activatable=True, selectable=True, hexpand=True)
                self.search_results.append(list_row)

        utils.set_window_cursor('default')
