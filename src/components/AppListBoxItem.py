from urllib import request
from gi.repository import Gtk, Adw, Gdk, GObject, Pango
from typing import Dict, List
import re

from ..models.AppListElement import AppListElement
from ..providers.providers_list import providers

class AppListBoxItem(Gtk.ListBoxRow):
    def __init__(self, list_element: AppListElement, **kwargs):
        super().__init__(**kwargs)

        self._app: AppListElement = list_element

        col = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        image = providers[list_element.provider].get_icon(list_element)
        image.set_pixel_size(45)
        col.append(image)

        app_details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER)
        app_details_box.append( Gtk.Label(label=f'<b>{list_element.name}</b>', halign=Gtk.Align.START, use_markup=True) )
        app_details_box.append( Gtk.Label(label=list_element.description, halign=Gtk.Align.START, lines=1, max_width_chars=100, ellipsize=Pango.EllipsizeMode.END) )
        
        col.append(app_details_box)
        self.set_child(col)