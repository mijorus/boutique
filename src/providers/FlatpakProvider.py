from ..lib import flatpak
from ..models.InstalledAppListElement import InstalledAppListElement
from ..models.Provider import Provider
from typing import List

class FlatpakProvider(Provider):
    def __init__(self):
        pass

    def list_installed(self) -> List[InstalledAppListElement]:
        output = [InstalledAppListElement(app['name'], app['description']) for app in flatpak.apps_list()]
        return output
