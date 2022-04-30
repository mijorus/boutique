from abc import ABC, abstractmethod
from typing import List
from .AppListElement import AppListElement
from gi.repository import Gtk

class Provider(ABC):

    @abstractmethod
    def list_installed(self) -> List[AppListElement]:
        pass

    @abstractmethod
    def get_icon(self, AppListElement) -> Gtk.Image:
        pass

    @abstractmethod
    async def uninstall(self, AppListElement) -> bool:
        pass
    
    def install(self, AppListElement) -> bool:
        pass
