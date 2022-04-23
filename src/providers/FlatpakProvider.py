from ..lib import flatpak
from ..models.InstalledAppListElement import InstalledAppListElement
from typing import List

class FlatpakProvider():
    def __init__(self):
        pass

    def list_installed(self) -> List[InstalledAppListElement]:
        app_list = flatpak.list_()

        list_installed = []
        for app in app_list:
            list_installed.append(InstalledAppListElement(app['name'], app['description']))

        print(list_installed)

        return list_installed
