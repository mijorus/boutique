from gi.repository import Gtk
from typing import Dict
from .providers.FlatpakProvider import FlatpakProvider
from .models.InstalledAppListElement import InstalledAppListElement


class InstalledAppsList(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.installed_apps_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        self.providers: Dict  = { 
            'flatpak': FlatpakProvider()
        }

        for p, provider in self.providers.items():
            installed: List[InstalledAppListElement] = provider.list_installed()

            for i in installed:
                self.installed_apps_list.append(Gtk.Label(label=i.name))

        self.set_child(self.installed_apps_list)



