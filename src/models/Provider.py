from abc import ABC, abstractmethod
from typing import List, Callable, Dict
from .AppListElement import AppListElement
from .Models import AppUpdateElement
from gi.repository import Gtk, Gio

class Provider(ABC):

    @abstractmethod
    def list_installed(self) -> List[AppListElement]:
        pass

    @abstractmethod
    def is_installed(self, el: AppListElement) -> bool:
        pass

    @abstractmethod
    def get_icon(self, AppListElement, repo: str=None, load_from_network: bool=False) -> Gtk.Image:
        pass

    @abstractmethod
    def uninstall(self, el: AppListElement, c: Callable[[bool], None]):
        pass

    @abstractmethod
    def install(self, el: AppListElement, c: Callable[[bool], None]):
        pass

    @abstractmethod
    def search(self, query: str) -> List[AppListElement]:
        pass

    @abstractmethod
    def get_long_description(self, el: AppListElement) ->  str:
        pass

    @abstractmethod
    def load_extra_data_in_appdetails(self, widget: Gtk.Widget, el: AppListElement):
        pass

    @abstractmethod
    def list_updateable(self) -> List[AppUpdateElement]:
        pass

    @abstractmethod
    def update(self, el: AppListElement, callback: Callable[[bool], None]):
        pass
    
    @abstractmethod
    def update_all(self, callback: Callable[[bool, str, bool], None]):
        pass

    @abstractmethod
    def run(self, el: AppListElement):
        pass

    @abstractmethod
    def can_install_file(self, filename: Gio.File) -> bool:
        pass

    @abstractmethod
    def install_file(self, filename: Gio.File, callback: Callable[[bool], None]) -> bool:
        pass

    @abstractmethod
    def create_list_element_from_file(self, file: Gio.File) -> AppListElement:
        pass

    @abstractmethod
    def get_app_sources(self, list_element: AppListElement) -> Dict[str, str]:
        pass

    # @abstractmethod
    # def get_active_source(self, list_element: AppListElement, source_id: str) -> AppListElement:
    #     pass