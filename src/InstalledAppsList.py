from gi.repository import Gtk, Pango
from typing import Dict, List
from .providers.FlatpakProvider import FlatpakProvider
from .models.InstalledAppListElement import InstalledAppListElement
from .models.Provider import Provider


class InstalledAppsList(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # A list containing all the "Providers" currently only Flatpak is supported
        # but I might need to add other ones in the future
        self.providers: List[Provider] = [ FlatpakProvider() ]

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.installed_apps_list = Gtk.ListBox()
        self.installed_apps_list.append( Gtk.Label(label='Installed applications', css_classes=['title-2']))
        

        for provider in self.providers:
            installed: List[InstalledAppListElement] = provider.list_installed()

            for i in installed:
                list_row = Gtk.ListBoxRow()

                col = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                col.append( Gtk.Image(resource="/it/mijorus/boutique/assets/flathub-badge-logo.svg", pixel_size=50) )

                app_details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER)
                app_details_box.append( Gtk.Label(label=f'<b>{i.name}</b>', halign=Gtk.Align.START, use_markup=True) )
                app_details_box.append( Gtk.Label(label=i.description, halign=Gtk.Align.START, lines=1, max_width_chars=100, ellipsize=Pango.EllipsizeMode.END) )
                
                col.append(app_details_box)

                list_row.set_child(col)
                self.installed_apps_list.append(list_row)

        self.main_box.append(self.installed_apps_list)
        self.set_child(self.main_box)



