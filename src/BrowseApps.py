import time
import threading
from typing import List, Dict
from .lib import flatpak, utils
from .models.AppListElement import AppListElement
from .models.Provider import Provider
from .providers.providers_list import providers
from .components.AppListBoxItem import AppListBoxItem
from .components.CustomComponents import CenteringBox

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
        self.search_results_slot = Gtk.Box(hexpand=True, vexpand=True)
        self.search_results_slot_placeholder = CenteringBox(hexpand=True, vexpand=True, spacing=5)
        self.search_results_slot_placeholder.append(Gtk.Image(icon_name='system-search-symbolic', css_classes=['large-icons']))
        self.search_results_slot_placeholder.append(Gtk.Label(label='Search for apps, games and more...', css_classes=['title-3']))

        self.search_results_slot.append(self.search_results_slot_placeholder)

        self.main_box.append(self.search_results_slot)

        clamp = Adw.Clamp(child=self.main_box, maximum_size=600, margin_top=10, margin_bottom=20)
        self.set_child(clamp)

    def on_activated_row(self, listbox: Gtk.ListBox, row: Gtk.ListBoxRow):
        """Emit and event that changes the active page of the Stack in the parent widget"""
        self.emit('selected-app', row._app)

    def on_search_entry_activated(self, widget: Gtk.SearchEntry):
        query = widget.get_text()
        self.search_results_slot.set_vexpand(False)

        if self.search_results_slot_placeholder.get_visible():
            self.search_results_slot_placeholder.set_visible(False)
            self.search_results_slot.remove(self.search_results_slot_placeholder)

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
        self.search_entry.set_editable(False)

        utils.set_window_cursor('wait')
        result: List[AppListElement] = provider.search(query)

        if not result:
            list_row = Gtk.Label(
                label='No apps found',
                margin_top=20,
                margin_bottom=20,
            )

            self.search_results.append(list_row)

        else:
            list_rows = []
            for i, app in enumerate(result):
                list_row = AppListBoxItem(app, activatable=True, selectable=True, hexpand=True, visible=False)
                self.search_results.append(list_row)

                list_row.load_icon(from_network=True)
                list_rows.append(list_row)

            for r in list_rows:
                r.set_visible(True)

        self.search_results.remove(spinner)
        self.search_entry.set_editable(True)

        utils.set_window_cursor('default')
