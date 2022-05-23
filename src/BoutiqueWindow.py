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

from gi.repository import Gtk, Adw, Gio


class BoutiqueWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Create a container stack 
        self.container_stack = Gtk.Stack()

        # Create the "main_stack" widget we will be using in the Window
        self.app_lists_stack = Adw.ViewStack()

        self.titlebar = Adw.HeaderBar()
        self.view_title_widget = Adw.ViewSwitcherTitle(stack=self.app_lists_stack)
        self.left_button = Gtk.Button(icon_name='go-previous', visible=False)

        self.titlebar.pack_start(self.left_button)
        
        self.titlebar.set_title_widget(self.view_title_widget)
        self.set_titlebar(self.titlebar)

        self.set_title('Boutique')
        self.set_default_size(600, 700)

        # Create the "stack" widget for the "installed apps" view
        self.installed_stack = Gtk.Stack()
        self.app_details = AppDetails()

        self.installed_apps_list = InstalledAppsList()
        self.installed_stack.add_child(self.installed_apps_list)

        self.installed_stack.set_visible_child(self.installed_apps_list)

        # Create the "stack" widget for the browse view
        self.browse_stack = Gtk.Stack()
        self.browse_apps = BrowseApps()

        self.browse_stack.add_child(self.browse_apps)
        
        # Add content to the main_stack
        utils.add_page_to_adw_stack(self.app_lists_stack, self.installed_stack, 'installed', 'Installed', 'computer-symbolic' )
        utils.add_page_to_adw_stack(self.app_lists_stack, self.browse_stack, 'browse', 'Browse' , 'globe-symbolic')

        self.container_stack.add_child(self.app_lists_stack)
        self.container_stack.add_child(self.app_details)
        self.set_child(self.container_stack)
        
        # Show details of an installed app
        self.installed_apps_list.connect('selected-app', self.on_selected_installed_app)
        # Show details of an app from global search
        self.browse_apps.connect('selected-app', self.on_selected_browsed_app)
        # come back to the list from the app details window
        self.app_details.connect('show_list', self.on_show_installed_list)
        # left arrow click
        self.left_button.connect('clicked', self.on_left_button_clicked)
        # change visible child of the app list stack
        self.app_lists_stack.connect('notify::visible-child', self.on_app_lists_stack_change)
        # change visible child of the container stack
        self.container_stack.connect('notify::visible-child', self.on_container_stack_change)

    def on_selected_installed_app(self, source: Gtk.Widget, list_element: AppListElement):
        """Show app details"""

        self.app_details.set_app_list_element(list_element)
        self.container_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        self.container_stack.set_visible_child(self.app_details)

    def on_selected_browsed_app(self, source: Gtk.Widget, list_element: AppListElement):
        """Show details for an app from global search"""

        self.app_details.set_app_list_element(list_element, load_icon_from_network=True)
        self.container_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        self.container_stack.set_visible_child(self.app_details)

    def on_selected_local_file(self, file: Gio.File):
        if self.app_details.set_from_local_file(file):
            self.container_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
            self.container_stack.set_visible_child(self.app_details)
        else:
            Gio.Notification.new('Unsupported file type: Boutique can\'t handle these types of files.')

    def on_show_installed_list(self, source: Gtk.Widget=None, _=None):
        self.container_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
        self.left_button.set_visible(False)

        self.installed_apps_list.refresh_list()
        self.installed_apps_list.refresh_upgradable()
        self.container_stack.set_visible_child(self.app_lists_stack)

    def on_show_browsed_list(self, source: Gtk.Widget=None, _=None):
        self.container_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
        self.left_button.set_visible(False)

        self.container_stack.set_visible_child(self.app_lists_stack)

    def on_left_button_clicked(self, widget):
        if self.app_lists_stack.get_visible_child() == self.installed_stack:
            if self.container_stack.get_visible_child() == self.app_details:
                self.on_show_installed_list()

        elif self.app_lists_stack.get_visible_child() == self.browse_stack:
            if self.container_stack.get_visible_child() == self.app_details:
                self.on_show_browsed_list()

    def on_app_lists_stack_change(self, widget, _):
        pass

    def on_container_stack_change(self, widget, _):
        in_app_details = self.container_stack.get_visible_child() == self.app_details
        self.left_button.set_visible(in_app_details)
        self.view_title_widget.set_visible(not in_app_details)