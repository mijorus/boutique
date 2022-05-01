from typing import List, Dict
from .models.AppListElement import AppListElement
from .lib import flatpak, utils
from .providers.providers_list import providers

from gi.repository import Gtk, Adw

class BrowseApps(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=20, margin_bottom=20)

        self.search_entry = Gtk.SearchEntry()

        self.search_entry.props.placeholder_text = 'Search for an app'
        self.search_entry.connect('search-changed', self.on_search_changed)

        self.main_box.append(self.search_entry)

        self.search_results: Gtk.ListBox|None = None
        self.search_results_slot = Gtk.Box()
        self.main_box.append(self.search_results_slot)

        clamp = Adw.Clamp(child=self.main_box, maximum_size=600, margin_top=10, margin_bottom=20)
        self.set_child(clamp)

    def on_search_changed(self, widget: Gtk.SearchEntry):
        query = widget.get_text()

        if self.search_results:
            self.search_results_slot.remove(self.search_results)

        if len(query) < 3:
            return

        self.search_results = Gtk.ListBox(css_classes=["boxed-list"])

        # Perform search across all the providers
        results: List[AppListElement] = []
        for p, provider in providers.items():
            provider_res: List[AppListElement] = provider.search(query)

            for app in provider_res:
                list_row = Gtk.ListBoxRow(activatable=True, selectable=True)
                list_row.set_child(Gtk.Label(label=app.name))

                self.search_results.append(list_row)

        self.search_results_slot.append(self.search_results)