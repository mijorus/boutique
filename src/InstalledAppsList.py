from urllib import request
from gi.repository import Gtk, Pango, GObject, Gio, GdkPixbuf, GLib, Adw
from typing import Dict, List
from .providers.providers_list import providers
from .models.AppListElement import AppListElement
from .models.Provider import Provider


class InstalledAppsList(Gtk.ScrolledWindow):
    __gsignals__ = {
      "selected-app": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object, )),
    }

    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.installed_apps_list_slot = Gtk.Box()
        
        self.installed_apps_list: Gtk.ListBox = None

        self.refresh_list()

        title_row = Gtk.Box(margin_bottom=5)
        title_row.append( Gtk.Label(label='Installed applications', css_classes=['title-2']) )
        
        self.main_box.append(title_row)
        self.main_box.append(self.installed_apps_list_slot)

        clamp = Adw.Clamp(child=self.main_box, maximum_size=600, margin_top=20, margin_bottom=20)
        self.set_child(clamp)

    def on_activated_row(self, listbox, row: Gtk.ListBoxRow):
        self.emit('selected-app', row._app)

    def refresh_list(self):
        if self.installed_apps_list:
            self.installed_apps_list_slot.remove(self.installed_apps_list)

        self.installed_apps_list= Gtk.ListBox(css_classes=["boxed-list"])

        for p, provider in providers.items():
            installed: List[AppListElement] = provider.list_installed()

            for i in installed:
                list_row = Adw.ActionRow(activatable=True, selectable=True)
                list_row._app: AppListElement = i

                col = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

                image = provider.get_icon(i)
                image.set_pixel_size(45)
                col.append(image)

                app_details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER)
                app_details_box.append( Gtk.Label(label=f'<b>{i.name}</b>', halign=Gtk.Align.START, use_markup=True) )
                app_details_box.append( Gtk.Label(label=i.description, halign=Gtk.Align.START, lines=1, max_width_chars=100, ellipsize=Pango.EllipsizeMode.END) )
                
                col.append(app_details_box)
                list_row.set_child(col)

                self.installed_apps_list.append(list_row)

        self.installed_apps_list_slot.append(self.installed_apps_list)
        self.installed_apps_list.connect('row-activated', self.on_activated_row)