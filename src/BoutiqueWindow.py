# window.py
#
# Copyright 2022 Lorenzo Paderi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from .InstalledAppsList import InstalledAppsList
from .AppDetails import AppDetails
from .models.AppListElement import AppListElement
from .lib import flatpak

from gi.repository import Gtk


class BoutiqueWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.titlebar = Gtk.HeaderBar()
        self.set_titlebar(self.titlebar)


        self.set_title('Boutique')
        self.set_default_size(600, 700)

        # Create the "stack" widget we will be using in the Window
        self.stack = Gtk.Stack()

        self.installed_apps_list = InstalledAppsList()
        self.stack.add_child(self.installed_apps_list)

        self.app_details = AppDetails()
        self.stack.add_child(self.app_details)

        self.set_child(self.stack)
        self.stack.set_visible_child(self.installed_apps_list)
        
        self.installed_apps_list.connect('selected-app', self.on_selected_app)
        self.app_details.connect('show_list', self.on_show_list)

    def on_selected_app(self, source, list_element: AppListElement):
        self.app_details.set_app_list_element(list_element)

        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        self.stack.set_visible_child(self.app_details)

    def on_show_list(self, source, _):
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
        self.stack.set_visible_child(self.installed_apps_list)
