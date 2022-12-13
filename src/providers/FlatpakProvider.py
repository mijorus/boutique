import logging
import random
import string
import threading
import urllib
import re
import requests
import html2text
import time
import subprocess
from typing import TypedDict
from xdg import DesktopEntry

from ..lib import flatpak, terminal
from ..lib.utils import log, cleanhtml, key_in_dict, gtk_image_from_url, qq, get_application_window
from ..models.AppListElement import AppListElement, InstalledStatus
from ..components.CustomComponents import LabelStart
from ..models.Provider import Provider
from ..models.Models import FlatpakHistoryElement, AppUpdateElement
from typing import List, Callable, Union, Dict, Optional, List
from gi.repository import GLib, Gtk, Gdk, GdkPixbuf, Gio, GObject, Adw

class FlatpakState(TypedDict):
    installed_status: InstalledStatus

class FlatpakProvider(Provider):
    def __init__(self):
        self.name = 'Flatpak'
        self.icon = Gtk.Image(resource="/it/mijorus/boutique/assets/flathub-badge-logo.svg")

        self.refresh_installed_status_callback: Optional[Callable] = None
        self.remote_ls_updatable_cache: Optional[List] = None
        self.list_updatables_cache: Optional[str] = None
        self.update_section_cache = None
        self.list_installed_cache = None
        self.do_updates_need_refresh = True
        self.ignored_patterns = [
            'org.gtk.Gtk3theme',
            'org.kde.PlatformTheme',
            'org.kde.WaylandDecoration',
            'org.kde.KStyle',
            'org.videolan.VLC.Plugin'
        ]

        self.flatpaks_state: dict[str, FlatpakState] = {}
        self.list_installed_list: List[AppListElement] = []

    def is_installed(self, list_element: AppListElement, alt_sources: list[AppListElement]=[]):
        ref = self.get_ref(list_element)
        i = flatpak.is_installed(ref)

        if not i:
            return i, None

        installed_origin = flatpak.get_ref_origin(list_element.id)

        if (list_element.extra_data['origin'] != installed_origin):
            if (alt_sources):
                for alt in alt_sources:
                    if alt.extra_data['origin'] == installed_origin:
                        alt_origin_info = flatpak.get_info(ref)
                        alt.extra_data['version'] = alt_origin_info['version']
                        return i, alt
            else:
                raise Exception('Missing origin ' + installed_origin)

        else:
            return i, None

    def list_installed(self) -> List[AppListElement]:
        output: list[AppListElement] = []

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

    def get_icon(self, list_element: AppListElement, repo='flathub', load_from_network: bool=False) -> Gtk.Image:
        icon_in_local_path = False
        local_file_path = None

        if 'origin' in list_element.extra_data and 'arch' in list_element.extra_data:
            try:
                repo = list_element.extra_data['origin']
                aarch = list_element.extra_data['arch']
                local_file_path = f'{GLib.get_home_dir()}/.local/share/flatpak/appstream/{repo}/{aarch}/active/icons/128x128/{list_element.id}.png'

            except Exception as e:
                log(e)

        if local_file_path and GLib.file_test(local_file_path, GLib.FileTest.EXISTS):
            image = Gtk.Image.new_from_file(local_file_path)
            image.set_pixel_size(45)
        else:
            image = self.icon
            remotes = flatpak.remotes_list()

            if load_from_network:
                pref_remote = 'flathub' if ('flathub' in list_element.extra_data['remotes']) else list_element.extra_data['remotes'][0]
                pref_remote_data = key_in_dict(remotes, pref_remote)

                if pref_remote_data and ('url' in pref_remote_data):
                    try:
                        url = re.sub(r'\/$', '', pref_remote_data['url'])
                        gtk_image_from_url(f'{url}/appstream/x86_64/icons/128x128/{urllib.parse.quote(list_element.id, safe="")}.png', image)
                    except Exception as e:
                        log(e)

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
                ref = self.get_ref(list_element)
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

    def search(self, query: str) -> List[AppListElement]:
        installed_apps = flatpak.apps_list()
        result = flatpak.search(query)

        output = []

        apps: Dict[str, list] = {}
        for app in result[0:100]:
            skip = False
            for i in self.ignored_patterns:
                if i in app['application']:
                    skip = True
                    break

            if skip:
                continue

            if not app['application'] in apps:
                apps[ app['application'] ] = []

            apps[ app['application'] ].append(app)

        for app_id, app_sources in apps.items():
            installed_status = InstalledStatus.NOT_INSTALLED
            for i in installed_apps:
                if i['application'] == app_id:
                    installed_status = InstalledStatus.INSTALLED
                    break

            remotes_map: Dict[str, str] = {}
            fk_remotes = flatpak.remotes_list()

            app_list_element_sources: List[AppListElement] = []
            preselected_app: Optional[AppListElement] = None

            for app_source in app_sources:
                branch_name = app_source["branch"]
                app_remotes = app_source['remotes'].split(',')

                for r in app_remotes:
                    if (r in fk_remotes):
                        fk_remote_title = fk_remotes[r]['title'] 

                        if len(app_sources) > 1:
                            fk_remote_title += f' ({branch_name})'

                        app_source['source_id'] = f'{r}:{app_source["application"]}/{flatpak.get_default_aarch()}/{app_source["branch"]}'
                        remotes_map[ app_source['source_id'] ] = fk_remote_title

                        source_list_element = AppListElement(
                            ( app_source['name'] ), 
                            ( app_source['description'] ), 
                            app_source['application'], 
                            'flatpak',
                            installed_status,
                            None,

                            version=app_source['version'],
                            branch=app_source['branch'],
                            origin=r,
                            remote=r,
                            source_id=app_source['source_id'],
                            remotes=app_remotes
                        )

                        output.append(source_list_element)
        return output

    def get_long_description(self, el: AppListElement) -> str:
        from_remote = key_in_dict(el.extra_data, 'origin')
        
        if ('remotes' in el.extra_data and 'flathub' in el.extra_data['remotes']):
            from_remote = 'flathub'

        appstream = flatpak.get_appstream(el.id, from_remote)

        output = ''
        if key_in_dict(appstream, 'description'):
            output = html2text.html2text(appstream['description'])

        return f'<b>{el.description}</b>\n\n{output}'.replace("&", "&amp;")

    def get_available_from_labels(self, list_element):
        element_remotes: List[str] = []
        if 'remotes' in list_element.extra_data:
            element_remotes.extend(list_element.extra_data['remotes'])
        else:
            element_remotes.append(list_element.extra_data['origin'])

        out = []
    
        for r in element_remotes:
            if (r in remotes):
                out.append(self.get_remote_link(r, list_element))

        return out
    
    def get_installed_from_source(self, el):
        return self.get_remote_link(el.extra_data['origin'], el) 
    
    def get_remote_link(self, r: str, el) -> str:
        remotes = flatpak.remotes_list()

        if (r in remotes):
            if 'homepage' in remotes[r]:
                remote_link = f'https://flathub.org/apps/details/{el.id}' if r == 'flathub' else remotes[r]['homepage']
                return remote_link
            else:
                return remotes[r]['title']
                
        return ''

    def load_extra_data_in_appdetails(self, widget, list_element: AppListElement):
        if 'origin' in list_element.extra_data:
            expander = Gtk.Expander(label="Show history", child=Gtk.Spinner())
            expander.ref = self.get_ref(list_element)
            expander._app = list_element
            expander.remote = list_element.extra_data['origin']
            expander.has_history = False
            expander.connect('notify::expanded', self.on_history_expanded)

            widget.append(expander)

    def get_ref(self, list_element: AppListElement):
        if 'ref' in list_element.extra_data:
            return list_element.extra_data['ref']

        return f'{list_element.id}/{flatpak.get_default_aarch()}/{list_element.extra_data["branch"]}'
        
    def create_history_expander(self, history, expander, success: bool):
        if (not success):
            expander.set_label('Couldn\'t load data')
            return
    
        expander.set_label('History')

        list_box = Gtk.ListBox(css_classes=["boxed-list"], show_separators=False, margin_top=10)
        for h in history:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin_top=5, margin_bottom=5, margin_start=5, margin_end=5)
            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

            title = Gtk.Label(label=h.date.split('+')[0], halign=Gtk.Align.START, css_classes=['heading'], wrap=True)
            subtitle = Gtk.Label(label=h.subject, halign=Gtk.Align.START, css_classes=['dim-label', 'caption'], selectable=True, wrap=True, max_width_chars=100)
            col.append(title)
            col.append(subtitle)
            row.append(col)

            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER, vexpand=True, hexpand=True, halign=Gtk.Align.END)
            install_label = qq(expander._app.installed_status == InstalledStatus.INSTALLED, 'Downgrade', 'Install')
            install_btn = Gtk.Button(label=install_label)
            # install_btn._app = list
            install_btn.connect('clicked', self.show_downgrade_dialog, {'commit': h.commit, 'list_element': expander._app})
            col.append(install_btn)
            row.append(col)

            list_box.append(row)

        expander.has_history = True
        expander.set_child(list_box)

    def async_load_app_history(self, expander: Gtk.Expander):
        success = True

        try:
            history: List[FlatpakHistoryElement] = flatpak.get_app_history(expander.ref, expander.remote)
        except Exception as e:
            logging.error(e)
            success = False

        GLib.idle_add(self.create_history_expander, history, expander, success)

    def on_history_expanded(self, expander: Gtk.Expander, state):
        if expander.has_history:
            return

        expander.set_label('Loading history...')
        if isinstance(expander.get_child(), Gtk.Spinner):
            expander.get_child().set_spinning(True)

        threading.Thread(target=self.async_load_app_history, args=(expander, )).start()

    def list_updatables(self) -> List[AppUpdateElement]:
        if not self.do_updates_need_refresh and (self.list_updatables_cache is not None):
            update_output = self.list_updatables_cache
        else:
            self.update_remote_ls_updatable_cache()
            update_output = terminal.sh(['flatpak', 'update', '--user'], return_stderr=True)
            self.list_updatables_cache = update_output
        
        if not '1.\t' in update_output:
            self.refresh_update_section_cache(None)
            return []

        self.refresh_update_section_cache(update_output)

        start_pattern = re.compile(r'^([0-9]+\.)')
        output = []

        if self.update_section_cache:
            for row in self.update_section_cache.split('\n'):
                row = row.strip()
                if not re.match(start_pattern, row):
                    break
                else:
                    cols = []
                    for i, col in enumerate(row.split('\t')):
                        col = col.strip()
                        if (i > 0) and len(col) > 0:
                            cols.append(col)


                    update_size = ''.join( re.findall(r'([0-9]|,)', cols[4], flags=re.A) ) if len(cols) > 3 else '0'
                    app_update_element = AppUpdateElement(cols[0], update_size, None)
                    output.append( app_update_element )

                    for rc in self.remote_ls_updatable_cache:
                        if rc['application'] == app_update_element.id:
                            app_update_element.to_version = rc['version']
                            break
        
        self.do_updates_need_refresh = False
        return output

    def update(self, list_element: AppListElement, callback: Callable):
        self.list_updatables_cache = None

        def update_task():
            ref = self.get_ref(list_element)
            success = False

            self.flatpaks_state[list_element.id] = {'installed_status': list_element.installed_status}

            try:
                terminal.sh(['flatpak', 'update', '--user', '--noninteractive', ref])
                list_element.set_installed_status(InstalledStatus.INSTALLED)
                self.remote_ls_updatable_cache = None
                self.do_updates_need_refresh = True
                success = True
            except Exception as e:
                logging.error(e)
                list_element.set_installed_status(InstalledStatus.ERROR)

            self.flatpaks_state[list_element.id] = {'installed_status': list_element.installed_status}

            if self.refresh_installed_status_callback:
                self.refresh_installed_status_callback(final=True)

            if callback:
                callback(success)

        list_element.set_installed_status(InstalledStatus.UPDATING)
        threading.Thread(target=update_task, daemon=True).start()

    def run(self, el: AppListElement):
        terminal.threaded_sh(['flatpak', 'run', '--user', el.id])

    def update_all(self, callback: Callable):
        def update_task(callback):
            success = False

            try:
                terminal.sh(['flatpak', 'update', '--user', '-y', '--noninteractive'])
                self.do_updates_need_refresh = True
                success = True
            except Exception as e:
                log(e)

            if callback:
                callback(success, 'flatpak')

        threading.Thread(target=update_task, daemon=True, args=(callback, )).start()

    def can_install_file(self, file: Gio.File):
        path: str = file.get_path()
        return path.endswith('flatpakref')

    def install_file(self, file, callback):
        def install_ref(path):
            log('installing ', path)
            terminal.sh(['flatpak', 'install', '--from', path, '--noninteractive', '--user'])
            if callback: callback(True)
            log('Installed!')

        threading.Thread(target=install_ref, args=(file.get_path(), ), daemon=True).start()

    def create_list_element_from_file(self, file: Gio.File) -> AppListElement:
        res = file.load_contents(None)
        contents: str = res.contents.decode('utf-8')

        props: Dict[str, str] = {}
        for line in contents.split('\n'):
            if not '=' in line: 
                continue

            keyval = line.split('=', maxsplit=1)
            props[ keyval[0].lower() ] = keyval[1]

        # @todo
        installed_status = InstalledStatus.INSTALLED if flatpak.is_installed(props['name']) else InstalledStatus.NOT_INSTALLED
        
        name = props['name']
        desc = props['title']

        if props['url'] == flatpak.FLATHUB_REPO_URL:
            try:
                appstream = flatpak.get_appstream(name, 'flathub')
                if 'name' in appstream:
                    name = appstream['name']
            except:
                pass

        list_element = AppListElement(name, desc, props['name'], 'flatpak', installed_status, 
            remotes=[ flatpak.find_remote_from_url(props['url']) ],
            branch=props['branch'],
            origin=flatpak.find_remote_from_url(props['url']),
            file_path=file.get_path()
        )

        return list_element

    def show_downgrade_dialog(self, button: Gtk.Button, data: dict):
        list_element: AppListElement = data['list_element']

        def install_old_version():
            terminal.sh(['flatpak', 'kill', list_element.id], return_stderr=True)
            self.refresh_installed_status_callback(status=InstalledStatus.UPDATING)
            
            try:
                terminal.sh(['flatpak', 'update', f'--commit={data["commit"]}', '-y', '--noninteractive', list_element.id])
                self.do_updates_need_refresh = True
                self.refresh_installed_status_callback(status=InstalledStatus.INSTALLED)
            except Exception as e:
                print(e)
                self.refresh_installed_status_callback(final=True, status=InstalledStatus.ERROR)

        def on_downgrade_dialog_response(dialog: Gtk.Dialog, response: int):
            if response == Gtk.ResponseType.YES:
                threading.Thread(target=install_old_version, daemon=True).start()

            dialog.destroy()

        action = qq(data['list_element'].installed_status.INSTALLED, 'downgrade', 'install')
        self.downgrade_dialog = Gtk.MessageDialog(
            # flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f'Do you really want to {action} "{data["list_element"].name}" ?',
            transient_for=get_application_window(),
            secondary_text=f'An older version might contain bugs and could have issues with newer configuration files.'
        )

        self.downgrade_dialog.connect('response', on_downgrade_dialog_response)
        self.downgrade_dialog.show()

    def get_selected_source(self, list_elements: list[AppListElement], source_id: str) -> AppListElement:
        for alt_source in list_elements:
            if source_id == self.create_source_id(alt_source):
                remote_ls_items = flatpak.remote_ls(updates_only=False, cached=True, origin=alt_source.extra_data['origin'])

                for rc in remote_ls_items:
                    if (rc['application'] == alt_source.id) and (rc['origin'] == alt_source.extra_data['origin']):
                        alt_source.extra_data['version'] = rc['version']
                        break

                return alt_source

        raise Exception('Missing list_element source!')

    def update_remote_ls_updatable_cache(self):
        """Updated the global remote_ls_cache varaible"""
        if self.remote_ls_updatable_cache is None:
            self.remote_ls_updatable_cache = []
            terminal.sh(['flatpak', 'update', '--appstream'], return_stderr=False)

            try:
                self.remote_ls_updatable_cache = flatpak.remote_ls(updates_only=True)
            except Exception as e:
                self.remote_ls_updatable_cache = []

    def is_updatable(self, app_id: str) -> bool:
        if self.update_section_cache == None:
            update_output = terminal.sh(['flatpak', 'update', '--user'], return_stderr=True)
            self.refresh_update_section_cache(update_output)

        return (app_id in self.update_section_cache)

    def refresh_update_section_cache(self, update_output: Optional[str]):
        self.update_section_cache = ''

        if update_output:
            update_sections = update_output.split('1.\t', maxsplit=1)

            if len(update_sections) > 1:
                update_section = '1.\t' + update_sections[1]
                self.update_section_cache = update_section
    
    def get_source_details(self, list_element: AppListElement):
        return (
            self.create_source_id(list_element), 
            f"{list_element.extra_data['origin']} ({list_element.extra_data['branch']})"
        )

    def create_source_id(self, list_element: AppListElement) -> str:
        return f"{list_element.extra_data['origin']}/{list_element.extra_data['branch']}"

    def set_refresh_installed_status_callback(self, callback: Optional[Callable]):
        self.refresh_installed_status_callback = callback

    def updates_need_refresh(self) -> bool:
        return self.do_updates_need_refresh

    def get_previews(self, el: AppListElement) -> list[Gtk.Widget]:
        def load_preview_image(url, image: Gtk.Image, button: Gtk.Button):
            gtk_image_from_url(screenshot_sizes[selected_size], image)
            button.set_visible(True)

        if el.extra_data['origin'] == 'flathub':
            appstream = flatpak.get_appstream(el.id, 'flathub')

            output = []
            if appstream and ('screenshots' in appstream):
                for screenshot_sizes in appstream['screenshots']:
                    selected_size = list(screenshot_sizes.keys())[0]
                    preview = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

                    image = Gtk.Image(pixel_size=400)
                    image_button = Gtk.Button(label='Open in the browser', visible=False, halign=Gtk.Align.CENTER)
                    image_button.connect('clicked', lambda w: Gtk.show_uri(None, screenshot_sizes[selected_size], time.time()))

                    preview.append(image)
                    preview.append(image_button)

                    output.append(preview)

                    threading.Thread(target=load_preview_image, daemon=True, args=(screenshot_sizes[selected_size], image, image_button)).start()

                return output

        return []