from urllib import request
from gi.repository import Gtk, Adw, Gdk, GObject, Pango
from typing import Dict, List, Optional
from ..lib.utils import cleanhtml
import re

from ..models.AppListElement import AppListElement
from ..providers.providers_list import providers

class AppListBoxItem(Gtk.ListBoxRow):
    def __init__(self, list_element: AppListElement, load_icon_from_network=False, **kwargs):
        super().__init__(**kwargs)

        self._app: AppListElement = list_element

        col = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        col.set_css_classes(['app-listbox-item'])

        self.image_container = Gtk.Box()
        col.append(self.image_container)

        app_details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER)
        app_details_box.append( 
            Gtk.Label(
                label=f'<b>{cleanhtml(list_element.name).replace("&", "")}</b>', 
                halign=Gtk.Align.START,
                use_markup=True, 
                max_width_chars=70, 
                ellipsize=Pango.EllipsizeMode.END
            )
        )

        desc = list_element.description if len(list_element.description) else 'No description provided'
        app_details_box.append( Gtk.Label(label=cleanhtml(desc), halign=Gtk.Align.START, lines=1, max_width_chars=100, ellipsize=Pango.EllipsizeMode.END) )

        self.update_version = Gtk.Label(
            label='0.10 > 0.20',
            margin_top=3,
            halign=Gtk.Align.START,
            css_classes=['subtitle'],
            visible=False
        )

        app_details_box.append(self.update_version)
        
        col.append(app_details_box)
        self.set_child(col)

    def load_icon(self, from_network: bool=False):
        image = providers[self._app.provider].get_icon(self._app, load_from_network=from_network)
        image.set_pixel_size(45)
        self.image_container.append( image )

    def set_update_version(self, text: Optional[str]):
        self.update_version.set_visible(text != None)

        if text:
            self.update_version.set_label(text)
