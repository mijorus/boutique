from abc import ABC, abstractmethod
from typing import List
from .InstalledAppListElement import InstalledAppListElement

class Provider(ABC):

    @abstractmethod
    def list_installed(self) -> List[InstalledAppListElement]:
        pass