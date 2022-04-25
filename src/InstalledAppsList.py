from urllib import request
from gi.repository import Gtk, Pango, GObject, Gio, GdkPixbuf, GLib
from typing import Dict, List
from .providers.FlatpakProvider import FlatpakProvider
from .models.AppListElement import AppListElement
from .models.Provider import Provider


class InstalledAppsList(Gtk.ScrolledWindow):
    __gsignals__ = {
      "selected-app": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object, )),
    }

    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # A list containing all the "Providers" currently only Flatpak is supported
        # but I might need to add other ones in the future
        self.providers: Dict[str, Provider] = { 
            'flatpak': FlatpakProvider() 
        }

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.installed_apps_list = Gtk.ListBox()

        title_row = Gtk.ListBoxRow(activatable=False, selectable=False)
        title_row.set_child( Gtk.Label(label='Installed applications', css_classes=['title-2']) )
        self.installed_apps_list.append(title_row)
        

        for p, provider in self.providers.items():
            installed: List[AppListElement] = provider.list_installed()

            for i in installed:
                list_row = Gtk.ListBoxRow(activatable=True, selectable=True)
                list_row._app: AppListElement = i

                col = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

                try:
                    # url = f'https://dl.flathub.org/repo/appstream/x86_64/icons/128x128/{i.id}.png'

                    image = Gtk.Image.new_from_file(f'{GLib.get_home_dir()}/.local/share/flatpak/app/{i.id}/current/active/files/share/app-info/icons/flatpak/128x128/{i.id}.png')
                    image.set_pixel_size(45)
                    col.append(image)
                except Exception as e:
                    print(e)

                    col.append( Gtk.Image(resource="/it/mijorus/boutique/assets/flathub-badge-logo.svg", pixel_size=45) )

                app_details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER)
                app_details_box.append( Gtk.Label(label=f'<b>{i.name}</b>', halign=Gtk.Align.START, use_markup=True) )
                app_details_box.append( Gtk.Label(label=i.description, halign=Gtk.Align.START, lines=1, max_width_chars=100, ellipsize=Pango.EllipsizeMode.END) )
                
                col.append(app_details_box)
                list_row.set_child(col)

                self.installed_apps_list.append(list_row)

        self.main_box.append(self.installed_apps_list)
        self.installed_apps_list.connect('row-activated', self.on_activated_row)

        self.set_child(self.main_box)

    def on_activated_row(self, listbox, row: Gtk.ListBoxRow):
        self.emit('selected-app', row._app)



