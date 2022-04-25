from ..lib import flatpak
from ..models.AppListElement import AppListElement
from ..models.Provider import Provider
from typing import List

class FlatpakProvider(Provider):
    def __init__(self):
        pass

    def list_installed(self) -> List[AppListElement]:
        output = []

        for app in flatpak.apps_list():
            output.append(
                AppListElement(app['name'], app['description'], app['application'])
            )

        return output
