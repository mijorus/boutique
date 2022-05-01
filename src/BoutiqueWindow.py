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
from .BrowseApps import BrowseApps
from .AppDetails import AppDetails
from .models.AppListElement import AppListElement
from .lib import flatpak, utils

from gi.repository import Gtk, Adw


class BoutiqueWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Create the "main_stack" widget we will be using in the Window
        self.main_stack = Adw.ViewStack()

        self.titlebar = Adw.HeaderBar()
        self.title_widget = Adw.ViewSwitcherTitle(stack=self.main_stack)
        self.left_button = Gtk.Button(icon_name='go-previous', visible=False)

        self.titlebar.pack_start(self.left_button)
        
        self.titlebar.set_title_widget(self.title_widget)
        self.set_titlebar(self.titlebar)

        self.set_title('Boutique')
        self.set_default_size(600, 700)

        # Create the "stack" widget for the "installed apps" view
        self.installed_stack = Gtk.Stack()

        self.installed_apps_list = InstalledAppsList()
        self.installed_stack.add_child(self.installed_apps_list)

        self.app_details = AppDetails()
        self.installed_stack.add_child(self.app_details)
        self.installed_stack.set_visible_child(self.installed_apps_list)

        # Create the "stack" widget for the browse view
        self.browse_stack = Gtk.Stack()
        self.browse_apps = BrowseApps()

        self.browse_stack.add_child(self.browse_apps)
        
        # Add content to the main_stack
        utils.add_page_to_adw_stack(self.main_stack, self.installed_stack, 'installed', 'Installed', 'computer-symbolic' )
        utils.add_page_to_adw_stack(self.main_stack, self.browse_stack, 'browse', 'Browse' , 'browser-download-symbolic')

        self.set_child(self.main_stack)
        
        # Connect signals
        self.installed_apps_list.connect('selected-app', self.on_selected_app)
        self.app_details.connect('show_list', self.on_show_list)
        self.left_button.connect('clicked', self.on_left_button_clicked)

    def on_selected_app(self, source: Gtk.Widget, list_element: AppListElement):
        """Show app details"""

        self.app_details.set_app_list_element(list_element)
        self.left_button.set_visible(True)
        self.installed_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        self.installed_stack.set_visible_child(self.app_details)

    def on_show_list(self, source: Gtk.Widget=None, _=None):
        self.installed_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
        self.left_button.set_visible(False)

        self.installed_apps_list.refresh_list()
        self.installed_stack.set_visible_child(self.installed_apps_list)

    def on_left_button_clicked(self, widget):
        if self.installed_stack.get_visible_child() == self.app_details:
            self.on_show_list()

