from ..lib import flatpak
from ..models.AppListElement import AppListElement
from ..models.Provider import Provider
from typing import List
from gi.repository import GLib, Gtk

class FlatpakProvider(Provider):
    def __init__(self):
        pass

    def list_installed(self) -> List[AppListElement]:
        output = []

        for app in flatpak.apps_list():
            output.append(
                AppListElement(app['name'], app['description'], app['application'], 'flatpak', ref=app['ref'])
            )

        return output

    def get_icon(self, list_element: AppListElement, repo='flathub'):
        repo = flatpak.get_ref_origin(list_element.extra_data['ref'])
        aarch = flatpak.get_default_aarch()
        local_file_path = f'{GLib.get_home_dir()}/.local/share/flatpak/appstream/{repo}/{aarch}/active/icons/128x128/{list_element.id}.png'
        icon_in_local_path = GLib.file_test(local_file_path, GLib.FileTest.EXISTS)

        if icon_in_local_path:
            image = Gtk.Image.new_from_file(local_file_path)
        else:
            image = Gtk.Image(resource="/it/mijorus/boutique/assets/flathub-badge-logo.svg")

        return image