import random
import string
import threading
import urllib
import re
import requests

from ..lib import flatpak
from ..lib.utils import log, cleanhtml, key_in_dict
from ..models.AppListElement import AppListElement, InstalledStatus
from ..models.Provider import Provider
from typing import List, Callable, Union
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

    def get_icon(self, list_element: AppListElement, repo='flathub', load_from_network: bool=False):

        def load_from_network_task(image_widget: Gtk.Image, list_element: AppListElement, remote: Union[dict, bool]=False):
            if not remote or 'url' not in remote:
                return

            url = re.sub(r'\/$', '', remote['url'])
            cache_dir = GLib.get_user_cache_dir()

            filename = cache_dir + '/' + (''.join(random.choice(string.ascii_letters) for i in range(10))) + '.png'

            try:
                response = requests.get(f'{url}/appstream/x86_64/icons/128x128/{urllib.parse.quote(list_element.id, safe="")}.png')
                response.raise_for_status()

                r = response.content

                GLib.file_set_contents(filename, r)
                image_widget.set_from_file(filename)
                GLib.unlink(filename)
            except Exception as e:
                log(e)

        icon_in_local_path = False

        if 'origin' in list_element.extra_data and 'arch' in list_element.extra_data:
            try:
                repo = list_element.extra_data['origin']
                aarch = list_element.extra_data['arch']
                local_file_path = f'{GLib.get_home_dir()}/.local/share/flatpak/appstream/{repo}/{aarch}/active/icons/128x128/{list_element.id}.png'
                icon_in_local_path = GLib.file_test(local_file_path, GLib.FileTest.EXISTS)
            except Exception as e:
                log(e)

        if icon_in_local_path:
            image = Gtk.Image.new_from_file(local_file_path)
        else:
            image = Gtk.Image(resource="/it/mijorus/boutique/assets/flathub-badge-logo.svg")
            remotes = flatpak.remotes_list()

            if load_from_network:
                pref_remote = 'flathub' if ('flathub' in list_element.extra_data['remotes']) else list_element.extra_data['remotes'][0]
                pref_remote_data = key_in_dict(remotes, pref_remote)

                thread = threading.Thread(
                    target=load_from_network_task, 
                    daemon=True, 
                    args=(image, list_element, pref_remote_data, )
                )

                thread.start()

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

    def search(self, query: str):
        installed_apps = flatpak.apps_list()
        result = flatpak.search(query)

        output = []
        ignored_patterns = [
            'org.gtk.Gtk3theme',
            'org.kde.PlatformTheme',
            'org.kde.WaylandDecoration',
            'org.kde.KStyle'
        ]

        for app in result[0:100]:
            skip = False
            for i in ignored_patterns:
                if i in app['application']:
                    skip = True
                    break

            if skip:
                continue

            installed_status = InstalledStatus.NOT_INSTALLED
            for i in installed_apps:
                if i['application'] == app['application']:
                    installed_status = InstalledStatus.INSTALLED
                    break

            output.append(
                AppListElement(
                    ( app['name'] ), 
                    ( app['description'] ), 
                    app['application'], 
                    'flatpak', 
                    installed_status,

                    verison=app['version'],
                    remotes=app['remotes'].split(','),
                )
            )

        return output