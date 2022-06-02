import time
import threading
from typing import List, Dict
from .lib import flatpak, utils
from .models.AppListElement import AppListElement
from .models.Models import SearchResultsItems
from .models.Provider import Provider
from .providers.providers_list import providers
from .components.AppListBoxItem import AppListBoxItem
from .components.CustomComponents import CenteringBox, NoAppsFoundRow

from gi.repository import Gtk, Adw, GObject, Gio, Gdk

class BrowseApps(Gtk.ScrolledWindow):
    __gsignals__ = {
      "selected-app": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object, )),
    }

    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=20, margin_bottom=20)

        self.search_entry = Gtk.SearchEntry()
        self.search_results: Gtk.ListBox = None

        self.search_entry.props.placeholder_text = 'Press "Enter" to search'
        self.search_entry.connect('activate', self.on_search_entry_activated)

        self.main_box.append(self.search_entry)

        self.search_results: Gtk.ListBox|None = None
        self.search_results_slot = Gtk.Box(hexpand=True, vexpand=True, orientation=Gtk.Orientation.VERTICAL)
        self.spinner = Gtk.Box(hexpand=True,halign=Gtk.Align.CENTER,margin_top=10,visible=False)
        self.spinner.append(Gtk.Spinner(spinning=True, margin_top=5, margin_bottom=5))

        self.search_results_slot.append(self.spinner)
        self.search_results_slot_placeholder = CenteringBox(hexpand=True, vexpand=True, spacing=5)
        self.search_results_slot_placeholder.append(Gtk.Image(icon_name='system-search-symbolic', css_classes=['large-icons']))
        self.search_results_slot_placeholder.append(Gtk.Label(label='Search for apps, games and more...', css_classes=['title-3']))

        self.search_results_slot.append(self.search_results_slot_placeholder)

        self.main_box.append(self.search_results_slot)

        clamp = Adw.Clamp(child=self.main_box, maximum_size=600, margin_top=10, margin_bottom=20)
        self.set_child(clamp)

    def on_activated_row(self, listbox: Gtk.ListBox, row: AppListBoxItem):
        """Emit and event that changes the active page of the Stack in the parent widget"""
        if not hasattr(row, '_app'):
            return 

        self.emit('selected-app', row._app, row._alt_sources)

    def on_search_entry_activated(self, widget: Gtk.SearchEntry):
        query = widget.get_text()

        if self.search_results_slot_placeholder.get_visible():
            self.search_results_slot_placeholder.set_visible(False)
            self.search_results_slot.remove(self.search_results_slot_placeholder)

        if self.search_results:
            self.search_results_slot.remove(self.search_results)

        if len(query) < 3:
            return

        widget.set_text('')

        # Perform search across all the providers
        Gio.Application.get_default().mark_busy()

        self.spinner.set_visible(True)
        utils.set_window_cursor('wait')
        self.search_entry.set_editable(False)
        threading.Thread(target=self.populate_search, args=(query, )).start()

    def populate_search(self, query: str):
        """Async function to populate the listbox without affecting the main thread"""

        provider_results: List[AppListElement] = []
        for p, provider in providers.items():
            provider_results.extend(provider.search(query))

        results_dict: dict[str, List[AppListElement]] = {}
        results: list[SearchResultsItems] = []
        for app in provider_results:
            if (not app.id in results_dict): results_dict[app.id] = []
            results_dict[app.id].append(app)

        for a, apps in results_dict.items():
            results.append( SearchResultsItems(a, apps) )

        self.search_results = Gtk.ListBox(hexpand=True, margin_top=10)
        self.search_results.set_css_classes(['boxed-list'])

        if not results:
            self.search_results.append(NoAppsFoundRow())

        else:
            load_img_threads: List[threading.Thread] = []

            for search_results_items in results:
                list_row = AppListBoxItem(
                    search_results_items.list_elements[0],
                    alt_sources=search_results_items.list_elements[1:],
                    activatable=True, 
                    selectable=True,
                    hexpand=True, 
                    visible=True
                )

                self.search_results.append(list_row)
                load_img_threads.append( threading.Thread(target=lambda r: r.load_icon(from_network=True), args=(list_row, )) )

            for t in load_img_threads: t.start()
            for t in load_img_threads: t.join()

        self.spinner.set_visible(False)
        self.search_results.connect('row-activated', self.on_activated_row)
        self.search_results_slot.append(self.search_results)
        self.search_entry.set_editable(True)
        utils.set_window_cursor('default')