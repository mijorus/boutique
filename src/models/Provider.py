from abc import ABC, abstractmethod
from typing import List
from .AppListElement import AppListElement

class Provider(ABC):

    @abstractmethod
    def list_installed(self) -> List[AppListElement]:
        pass