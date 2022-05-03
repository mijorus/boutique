from typing import List, Dict
from .lib import flatpak, utils
from .models.AppListElement import AppListElement
from .providers.providers_list import providers
from .components.AppListBoxItem import AppListBoxItem

from gi.repository import Gtk, Adw, GObject

class BrowseApps(Gtk.ScrolledWindow):
    __gsignals__ = {
      "selected-app": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object, )),
    }

    def __init__(self):
        super().__init__()

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=20, margin_bottom=20)

        self.search_entry = Gtk.SearchEntry()

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

        self.search_results = Gtk.ListBox(css_classes=["boxed-list"], hexpand=True, margin_top=10)

        # Perform search across all the providers
        results: List[AppListElement] = []
        for p, provider in providers.items():
            result: List[AppListElement] = provider.search(query)

            for app in result:
                list_row = AppListBoxItem(app, load_icon_from_network=True, activatable=True, selectable=True)
                self.search_results.append(list_row)

        self.search_results_slot.append(self.search_results)
        self.search_results.connect('row-activated', self.on_activated_row)