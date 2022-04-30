from ..lib import flatpak
from ..models.AppListElement import AppListElement, InstalledStatus
from ..models.Provider import Provider
from typing import List, Callable
from gi.repository import GLib, Gtk

class FlatpakProvider(Provider):
    def __init__(self):
        pass

    def list_installed(self) -> List[AppListElement]:
        output = []

        for app in flatpak.apps_list():
            output.append(
                AppListElement(
                    app['name'], 
                    app['description'], 
                    app['application'], 
                    'flatpak', 
                    InstalledStatus.INSTALLED,

                    ref=app['ref'], 
                    origin=app['origin'],
                    arch=app['arch'],
                )
            )

        return output

    def get_icon(self, list_element: AppListElement, repo='flathub'):
        repo = list_element.extra_data['origin']
        aarch = list_element.extra_data['arch']
        local_file_path = f'{GLib.get_home_dir()}/.local/share/flatpak/appstream/{repo}/{aarch}/active/icons/128x128/{list_element.id}.png'
        icon_in_local_path = GLib.file_test(local_file_path, GLib.FileTest.EXISTS)

        if icon_in_local_path:
            image = Gtk.Image.new_from_file(local_file_path)
        else:
            image = Gtk.Image(resource="/it/mijorus/boutique/assets/flathub-badge-logo.svg")

        return image

    def uninstall(self, list_element: AppListElement, callback: Callable[[bool], None]=None):
        success = False

        def after_uninstall(_: bool):
            list_element.set_installed_status(InstalledStatus.NOT_INSTALLED)
            
            if callback:
                callback(_)

        try:
            flatpak.remove(
                list_element.extra_data['ref'], 
                list_element.id, 
                lambda _: after_uninstall(True)
            )
            
            success = True
        except Exception as e:
            print(e)
            after_uninstall(False)
            list_element.set_installed_status(InstalledStatus.ERROR)

        return success

    def install(self, list_element: AppListElement) -> bool:
        success = False

        try:
            flatpak.install(list_element.extra_data['origin'], list_element.id)
            list_element.set_installed_status(InstalledStatus.INSTALLED)
            success = True
        except Exception as e:
            print(e)
        
        return success
