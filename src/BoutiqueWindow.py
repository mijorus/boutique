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
from .lib import flatpak

from gi.repository import Gtk


class BoutiqueWindow(Gtk.ApplicationWindow):
    # __gtype_name__ = 'BoutiqueWindow'

    # label = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_default_size(400, 600)

        apps_list = InstalledAppsList()
        self.set_child(apps_list)


