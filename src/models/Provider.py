from abc import ABC, abstractmethod
from typing import List, Callable
from .AppListElement import AppListElement
from .Models import AppUpdateElement
from gi.repository import Gtk

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
    def list_upgradable(self) -> List[AppUpdateElement]:
        pass