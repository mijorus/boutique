from abc import ABC, abstractmethod
from typing import List, Callable
from .AppListElement import AppListElement
from gi.repository import Gtk

class Provider(ABC):

    @abstractmethod
    def list_installed(self) -> List[AppListElement]:
        pass

    @abstractmethod
    def get_icon(self, AppListElement, repo: str=None, load_from_network: bool=False) -> Gtk.Image:
        pass

    @abstractmethod
    def uninstall(self, el: AppListElement, c: Callable[[bool], None]):
        pass
    
    def install(self, el: AppListElement, c: Callable[[bool], None]):
        pass

    def search(self, query: str) -> List[AppListElement]:
        pass

    def get_long_description(self, el: AppListElement) ->  str:
        pass