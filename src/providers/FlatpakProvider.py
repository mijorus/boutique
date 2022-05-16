import random
import string
import threading
import urllib
import re
import requests
import html2text

from ..lib import flatpak, terminal
from ..lib.utils import log, cleanhtml, key_in_dict, gtk_image_from_url
from ..models.AppListElement import AppListElement, InstalledStatus
from ..models.Provider import Provider
from ..models.Models import FlatpakHistoryElement, AppUpdateElement
from typing import List, Callable, Union, Dict
from gi.repository import GLib, Gtk, Gdk, GdkPixbuf, Gio

class FlatpakProvider(Provider):
    def __init__(self):
        pass

    def is_installed(self, list_element: AppListElement):
        return flatpak.is_installed(self.get_ref(list_element))

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
                    version=app['version'],
                )
            )

        return output

    def get_icon(self, list_element: AppListElement, repo='flathub', load_from_network: bool=False):

        def load_from_network_task(image_widget: Gtk.Image, list_element: AppListElement, remote: Union[dict, bool]=False):
            if not remote or 'url' not in remote:
                return

            url = re.sub(r'\/$', '', remote['url'])

            try:
                gtk_image_from_url(f'{url}/appstream/x86_64/icons/128x128/{urllib.parse.quote(list_element.id, safe="")}.png', image_widget)
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
                self.get_ref(list_element), 
                list_element.id, 
                lambda _: after_uninstall(True)
            )
            
            success = True
        except Exception as e:
            print(e)
            after_uninstall(False)
            list_element.set_installed_status(InstalledStatus.ERROR)

        return success

    def install(self, list_element: AppListElement, callback: Callable[[bool], None]=None):
        def install_thread(list_element: AppListElement, callback: Callable):
            try:
                ref = f'{list_element.id}/{flatpak.get_default_aarch()}/{list_element.extra_data["branch"]}'
                list_element.extra_data['ref'] = ref
                flatpak.install(list_element.extra_data['origin'], ref)
                list_element.set_installed_status(InstalledStatus.INSTALLED)

                if callback: callback(True)

            except Exception as e:
                print(e)
                list_element.set_installed_status(InstalledStatus.ERROR)
                if callback: callback(False)

        if not 'origin' in list_element.extra_data:
            raise Exception('Missing "origin" in list_element')

        thread = threading.Thread(target=install_thread, args=(list_element, callback, ), daemon=True)
        thread.start()

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

                    version=app['version'],
                    branch=app['branch'],
                    remotes=app['remotes'].split(','),
                    origin=app['remotes'].split(',')[0],
                )
            )

        return output

    def get_long_description(self, el: AppListElement) -> str:
        appstream = flatpak.get_appstream(el.id, key_in_dict(el.extra_data, 'origin'))

        output = ''
        if key_in_dict(appstream, 'description'):
            output = html2text.html2text(appstream['description'])

        return f'<b>{el.description}</b>\n\n{output}'.replace("&", "&amp;")

    def load_extra_data_in_appdetails(self, widget, list_element: AppListElement):
        remotes = flatpak.remotes_list()
        if 'origin' in list_element.extra_data:

            element_remotes: List[str] = []
            if 'remotes' in list_element.extra_data:
                element_remotes.extend(list_element.extra_data['remotes'])
            else:
                element_remotes.append(list_element.extra_data['origin'])
            

            source_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_bottom=10)
            source_row.append( Gtk.Label(label='Available from:', css_classes=['heading'], halign=Gtk.Align.START))
            
            for r in element_remotes:
                if (r in remotes) and 'homepage' in remotes[r]:
                    source_heading = Gtk.Label(css_classes=['heading'], halign=Gtk.Align.START)
                    source_heading.set_markup(f"""<a href="{remotes[r]['homepage']}">{remotes[r]['title']}</a>""")
                    source_row.append(source_heading)
                else:
                    source_row.append(Gtk.Label( label=f"""{remotes['origin']['title']}""", halign=Gtk.Align.START))

            widget.append(source_row)

            expander = Gtk.Expander(label="Show history", child=Gtk.Spinner())
            expander.ref = self.get_ref(list_element)
            expander.remote = list_element.extra_data['origin']
            expander.has_history = False
            expander.connect('notify::expanded', self.on_history_expanded)
            
            widget.append(expander)

    def get_ref(self, list_element: AppListElement):
        if 'ref' in list_element.extra_data:
            return list_element.extra_data['ref']

        return f'{list_element.id}/{flatpak.get_default_aarch()}/{list_element.extra_data["branch"]}'

    def on_history_expanded(self, expander: Gtk.Expander, state):
        def create_log_expander(expander: Gtk.Expander):
            expander.set_label('Loading history...')
            if isinstance(expander.get_child(), Gtk.Spinner):
                expander.get_child().set_spinning(True)

            try:
                history: List[FlatpakHistoryElement] = flatpak.get_app_history(expander.ref, expander.remote)
            except Exception as e:
                log(e)
                expander.set_label('Couldn\'t load history data')
                return

            expander.set_label('History')

            list_box = Gtk.ListBox(css_classes=["boxed-list"], show_separators=False, margin_top=10)
            for h in history:
                row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=5, margin_bottom=5, margin_start=5)
                row_title = Gtk.Label(label=h.date.split('+')[0], halign=Gtk.Align.START, css_classes=['heading'])
                row_value = Gtk.Label(label=h.subject, halign=Gtk.Align.START, css_classes=['dim-label', 'caption'], selectable=True, wrap=True)
                row.append(row_title)
                row.append(row_value)

                list_box.append(row)

            expander.has_history = True
            expander.set_child(list_box)

        if expander.has_history:
            return

        threading.Thread(target=create_log_expander, args=(expander, )).start()

    def list_updatable(self) -> List[AppUpdateElement]:
        update_output = terminal.sh(['flatpak', 'update', '--user'], return_stderr=True, hide_err=True)
        
        if not '1.\t' in update_output:
            return []

        update_section = update_output.split('1.\t', maxsplit=1)[1]
        update_section = '1.\t' + update_section

        start_pattern = re.compile(r'^([0-9]+\.)')
        output = []
        for row in update_section.split('\n'):
            row = row.strip()
            if not re.match(start_pattern, row):
                break
            else:
                cols = []
                for i, col in enumerate(row.split('\t')):
                    col = col.strip()
                    if not re.match(start_pattern, col) and len(col) > 0:
                        cols.append(col)

                update_size = ''.join( re.findall(r'([0-9]|,)',cols[4], flags=re.A) )
                output.append( AppUpdateElement(cols[0], update_size))

        return output

    def update(self, list_element: AppListElement, callback: Callable):
        def update_task(list_element: AppListElement, callback: Callable):
            ref = self.get_ref(list_element)
            success = False

            try:
                terminal.sh(['flatpak', 'update', '--user', '--noninteractive', ref])
                list_element.set_installed_status(InstalledStatus.INSTALLED)
                success = True
            except Exception as e:
                print(e)
                list_element.set_installed_status(InstalledStatus.ERROR)

            if callback:
                callback(success)

        list_element.set_installed_status(InstalledStatus.UPDATING)
        threading.Thread(target=update_task, daemon=True, args=(list_element, callback, )).start()

    def run(self, el: AppListElement):
        terminal.threaded_sh(['flatpak', 'run', '--user', el.id])

    def update_all(self, callback: Callable):
        def update_task(callback):
            success = False

            try:
                terminal.sh(['flatpak', 'update', '--user', '-y', '--noninteractive'])
                success = True
            except Exception as e:
                print(e)

            if callback:
                callback(success, 'flatpak')

        threading.Thread(target=update_task, daemon=True, args=(callback, )).start()

    def can_install_file(self, file: Gio.File):
        path: str = file.get_path()
        return path.endswith('flatpakref')

    def install_file(self, file, callback):
        def install_ref(path):
            print('installing ', path)
            terminal.sh(['flatpak', 'install', '--from', path, '--noninteractive', '--user'])
            print('Installed!')

        threading.Thread(target=install_ref, args=(file.get_path(), ), daemon=True).start()

    def create_list_element_from_file(self, file: Gio.File) -> AppListElement:
        res = file.load_contents(None)
        contents: str = res.contents.decode('utf-8')

        props: Dict[str, str] = {}
        for line in contents.split('\n'):
            keyval = line.split('=', maxsplit=1)
            props[ keyval[0].lower() ] = keyval[1]

        # @todo
        installed_status = InstalledStatus.INSTALLED if flatpak.is_installed(props['name']) else InstalledStatus.NOT_INSTALLED
        list_element = AppListElement(props['name'], props['title'], props['name'], 'flathub', installed_status)