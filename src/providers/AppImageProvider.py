import random
import string
import threading
import urllib
import re
import requests
import html2text

from ..lib import flatpak, terminal
from ..lib.utils import log, cleanhtml, key_in_dict, gtk_image_from_url, qq, get_application_window
from ..models.AppListElement import AppListElement, InstalledStatus
from ..components.CustomComponents import LabelStart
from ..models.Provider import Provider
from ..models.Models import FlatpakHistoryElement, AppUpdateElement
from typing import List, Callable, Union, Dict, Optional, List
from gi.repository import GLib, Gtk, Gdk, GdkPixbuf, Gio, GObject

class AppImageProvider(Provider):
    def __init__(self):
        # refresh_installed_status_callback: Callable
        pass

    def list_installed(self) -> List[AppListElement]:
        return []

    def is_installed(self, el: AppListElement, alt_sources: list[AppListElement]=[]) -> Tuple[bool, AppListElement]:
        pass

    def get_icon(self, AppListElement, repo: str=None, load_from_network: bool=False) -> Gtk.Image:
        pass

    def uninstall(self, el: AppListElement, c: Callable[[bool], None]):
        pass

    def install(self, el: AppListElement, c: Callable[[bool], None]):
        pass

    def search(self, query: str) -> List[AppListElement]:
        pass

    def get_long_description(self, el: AppListElement) ->  str:
        pass

    def load_extra_data_in_appdetails(self, widget: Gtk.Widget, el: AppListElement):
        pass

    def list_updatables(self, from_cache=False) -> List[AppUpdateElement]:
        pass

    def update(self, el: AppListElement, callback: Callable[[bool], None]):
        pass
    
    def update_all(self, callback: Callable[[bool, str, bool], None]):
        pass

    def updates_need_refresh(self) -> bool:
        pass

    def run(self, el: AppListElement):
        pass

    def can_install_file(self, file: Gio.File) -> bool:
        path: str = file.get_path()
        return path.endswith('appimage')

    def is_updatable(self, app_id: str) -> bool:
        pass

    def install_file(self, filename: Gio.File, callback: Callable[[bool], None]) -> bool:
        pass

    def create_list_element_from_file(self, file: Gio.File) -> AppListElement:
        pass

    def get_selected_source(self, list_element: list[AppListElement], source_id: str) -> AppListElement:
        pass

    def get_source_details(self, list_element: AppListElement) -> tuple[str, str]:
        pass
    
    def set_refresh_installed_status_callback(self, callback: Optional[Callable]):
        pass