from gi.repository import Gtk
from typing import Dict, List
from .providers.FlatpakProvider import FlatpakProvider
from .models.InstalledAppListElement import InstalledAppListElement
from .models.Provider import Provider


class InstalledAppsList(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.installed_apps_list = Gtk.ListBox()
        
        self.providers: List[Provider] = [ FlatpakProvider() ]

        for provider in self.providers:
            installed: List[InstalledAppListElement] = provider.list_installed()

            for i in installed:
                row = Gtk.ListBoxRow()
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                
                logo = Gtk.Image(resource="/it/mijorus/boutique/assets/flathub-badge-logo.svg")
                label = Gtk.Label(label=i.name)

                box.append(logo)
                box.append(label)

                row.set_child(box)

                self.installed_apps_list.append(row)

        self.set_child(self.installed_apps_list)



