import random
import string
import threading
import logging
import urllib
import re
import os
import shutil
import time
import hashlib
import requests
import html2text
import subprocess
import filecmp
from xdg import DesktopEntry

from ..lib import flatpak, terminal
from ..models.AppListElement import AppListElement, InstalledStatus
from ..lib.utils import log, cleanhtml, key_in_dict, gtk_image_from_url, qq, get_application_window, get_giofile_content_type, get_gsettings, create_dict
from ..components.CustomComponents import LabelStart
from ..models.Provider import Provider
from ..models.Models import FlatpakHistoryElement, AppUpdateElement
from typing import List, Callable, Union, Dict, Optional, List, TypedDict
from gi.repository import GLib, Gtk, Gdk, GdkPixbuf, Gio, GObject, Pango

class ExtractedAppImage():
    desktop_entry: Optional[DesktopEntry.DesktopEntry]
    extraction_folder: Gio.File
    container_folder: Gio.File
    appimage_file: Gio.File
    desktop_file: Gio.File

class AppImageProvider(Provider):
    def __init__(self):
        # refresh_installed_status_callback: Callable
        pass

    def list_installed(self) -> List[AppListElement]:
        default_folder_path = self.get_appimages_default_destination_path()
        output = []
        
        try:
            folder = Gio.File.new_for_path(default_folder_path)
            desktop_files_dir = f'{GLib.get_home_dir()}/.local/share/applications/'

            for file_name in os.listdir(desktop_files_dir):
                gfile = Gio.File.new_for_path(desktop_files_dir + f'/{file_name}')

                try:
                    if get_giofile_content_type(gfile) == 'application/x-desktop':

                        entry = DesktopEntry.DesktopEntry(filename=gfile.get_path())
                        if entry.getExec().startswith(default_folder_path) and GLib.file_test(entry.getExec(), GLib.FileTest.EXISTS):
                            output.append(AppListElement(
                                name=entry.getName() + ' (AppImage)',
                                description=entry.getComment(),
                                icon=entry.getIcon(),
                                app_id=entry.getExec(),
                                installed_status=InstalledStatus.INSTALLED,
                                file_path=entry.getExec(),
                                provider='appimage',
                                desktop_entry=entry
                            ))

                except Exception as e:
                    logging.warn(e)

        except Exception as e:
            logging.error(e)

        return output

    def is_installed(self, el: AppListElement, alt_sources: list[AppListElement]=[]) -> tuple[bool, Optional[AppListElement]]:
        if 'file_path' in el.extra_data:
            for file_name in os.listdir(self.get_appimages_default_destination_path()):
                installed_gfile = Gio.File.new_for_path(self.get_appimages_default_destination_path() + '/' + file_name)
                loaded_gfile = Gio.File.new_for_path(el.extra_data['file_path'])

                if get_giofile_content_type(installed_gfile) == 'application/vnd.appimage':
                    if filecmp.cmp(installed_gfile.get_path(), loaded_gfile.get_path(), shallow=False):
                        el.extra_data['file_path'] = installed_gfile.get_path()
                        return True, None

        return False, None

    def get_icon(self, el: AppListElement, repo: str=None, load_from_network: bool=False) -> Gtk.Image:
        icon_path = None

        if 'desktop_entry' in el.extra_data:
            icon_path = el.extra_data['desktop_entry'].getIcon()

        if icon_path and os.path.exists(icon_path):
            return Gtk.Image.new_from_file(icon_path)
        else:
            icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
            
            if ('desktop_entry' in el.extra_data) and icon_theme.has_icon(el.extra_data['desktop_entry'].getIcon()):
                return Gtk.Image.new_from_icon_name(el.extra_data['desktop_entry'].getIcon())

            return Gtk.Image(resource="/it/mijorus/boutique/assets/App-image-logo-bw.svg")

    def uninstall(self, el: AppListElement, callback: Callable[[bool], None]):
        try:
            os.remove(el.extra_data['file_path'])
            os.remove(el.extra_data['desktop_entry'].getFileName())
            el.set_installed_status(InstalledStatus.NOT_INSTALLED)

            callback(True)
        except Exception as e:
            callback(False)
            logging.error(e)

    def install(self, el: AppListElement, c: Callable[[bool], None]):
        pass

    def search(self, query: str) -> List[AppListElement]:
        return []

    def get_long_description(self, el: AppListElement) ->  str:
        return ''

    def load_extra_data_in_appdetails(self, widget: Gtk.Widget, list_element: AppListElement):
        source_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_bottom=10)

        if 'file_path' in list_element.extra_data:
            source_row.append( LabelStart(label='File:', css_classes=['heading']) )
            source_row.append( 
                LabelStart(
                    label=list_element.extra_data['file_path'], 
                    margin_bottom=20,
                    max_width_chars=60, 
                    ellipsize=Pango.EllipsizeMode.MIDDLE,
                    selectable=True,
                ) 
            )

        widget.append(source_row)

    def list_updatables(self) -> List[AppUpdateElement]:
        return []

    def update(self, el: AppListElement, callback: Callable[[bool], None]):
        pass
    
    def update_all(self, callback: Callable[[bool, str, bool], None]):
        pass

    def updates_need_refresh(self) -> bool:
        return False

    def run(self, el: AppListElement):
        if self.get_appimages_default_destination_path() in el.extra_data['file_path']:
            terminal.threaded_sh([f'{el.extra_data["file_path"]}'], force=True)

    def can_install_file(self, file: Gio.File) -> bool:
        return get_giofile_content_type(file) == 'application/vnd.appimage'

    def is_updatable(self, app_id: str) -> bool:
        pass

    def install_file(self, list_element: AppListElement, callback: Callable[[bool], None]) -> bool:
        def install_job():
            list_element.installed_status = InstalledStatus.INSTALLING

            extracted_appimage = None

            try:
                # desktop_entry, extraction_folder, appimage_file, desktop_file = self.extract_appimage(file_path=list_element.extra_data['file_path'])
                extracted_appimage = self.extract_appimage(file_path=list_element.extra_data['file_path'])
                dest_file_info = extracted_appimage.appimage_file.query_info('*', Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS)

                if extracted_appimage.extraction_folder.query_exists():

                    # Move .appimage to its default location
                    appimages_destination_path = self.get_appimages_default_destination_path()

                    # how the appimage will be called
                    safe_app_name = f'boutique_{dest_file_info.get_name()}'
                    if extracted_appimage.desktop_entry:
                        safe_app_name = f'{terminal.sanitize(extracted_appimage.desktop_entry.getName())}_{dest_file_info.get_name()}'

                    dest_appimage_file = Gio.File.new_for_path(appimages_destination_path + '/' + safe_app_name + '.appimage')

                    if extracted_appimage.appimage_file.copy(
                        dest_appimage_file, 
                        Gio.FileCopyFlags.OVERWRITE, 
                        None, None, None, None
                    ):
                        log(f'file copied to {appimages_destination_path}')

                        os.chmod(dest_appimage_file.get_path(), 0o755)
                        list_element.extra_data['file_path'] = dest_appimage_file.get_path()

                        # copy the icon file
                        icon_file = None
                        dest_icon_file_path = 'applications-other' # a default icon

                        if extracted_appimage.desktop_entry:
                            icon_file = f'{extracted_appimage.extraction_folder.get_path()}/{extracted_appimage.desktop_entry.getIcon()}.png'
                            dest_icon_file_path = f'{appimages_destination_path}/icons/{dest_file_info.get_name()}.png'

                        if icon_file and os.path.exists(icon_file):
                            if not os.path.exists(f'{appimages_destination_path}/icons'):
                                os.mkdir(f'{appimages_destination_path}/icons')

                            shutil.copy(icon_file, dest_icon_file_path)

                        # Move .desktop file to its default location
                        desktop_files_destination_path = GLib.get_home_dir() + '/.local/share/applications'
                        dest_destop_file_path = f'{desktop_files_destination_path}/{safe_app_name}.desktop'
                        dest_destop_file_path = dest_destop_file_path.replace(' ', '_')

                        with open(extracted_appimage.desktop_file.get_path(), 'r') as desktop_file_python:
                            desktop_file_content = desktop_file_python.read()

                            desktop_file_content = re.sub(
                                r'Exec=.*$',
                                f"Exec={dest_appimage_file.get_path()}",
                                desktop_file_content,
                                flags=re.MULTILINE
                            )

                            desktop_file_content = re.sub(
                                r'Icon=.*$',
                                f"Icon={dest_icon_file_path}",
                                desktop_file_content,
                                flags=re.MULTILINE
                            )
                            

                            final_app_name = extracted_appimage.appimage_file.get_basename()
                            if extracted_appimage.desktop_entry:
                                final_app_name = f"{extracted_appimage.desktop_entry.getName()} ({extracted_appimage.desktop_entry.get('X-AppImage-Version')})"

                            desktop_file_content = re.sub(
                                r'Name=.*$',
                                f"Name={final_app_name}",
                                desktop_file_content,
                                flags=re.MULTILINE
                            )

                            with open(dest_destop_file_path, 'w+') as desktop_file_python_dest:
                                desktop_file_python_dest.write(desktop_file_content)

                        if os.path.exists(dest_destop_file_path):
                            log('desktop file copied to ' + desktop_files_destination_path)
                            list_element.extra_data['desktop_entry'] = DesktopEntry.DesktopEntry(filename=dest_destop_file_path)
                            list_element.installed_status = InstalledStatus.INSTALLED

            except Exception as e:
                try:
                    self.post_file_extraction_cleanup(extracted_appimage)
                except Exception as e:
                    pass

                list_element.installed_status = InstalledStatus.ERROR
                raise e

            self.post_file_extraction_cleanup(extracted_appimage)
            callback(list_element.installed_status == InstalledStatus.INSTALLED)

        threading.Thread(target=install_job, daemon=True).start()
        return True

    def create_list_element_from_file(self, file: Gio.File) -> AppListElement:
        app_name: str = file.get_parse_name().split('/')[-1]
        app_name = re.sub(r'\.appimage$', '', app_name, flags=re.IGNORECASE)
        app_name = re.sub(r'\.x86_64$', '', app_name, flags=re.IGNORECASE)

        return AppListElement(
            name=app_name, 
            description='', 
            app_id=hashlib.md5(open(file.get_path(), 'rb').read()).hexdigest(), 
            provider='appimage', 
            installed_status=InstalledStatus.NOT_INSTALLED,
            file_path=file.get_path()
        )

    def get_selected_source(self, list_element: list[AppListElement], source_id: str) -> AppListElement:
        pass

    def get_source_details(self, list_element: AppListElement) -> tuple[str, str]:
        pass
    
    def set_refresh_installed_status_callback(self, callback: Optional[Callable]):
        pass

    def post_file_extraction_cleanup(self, extraction: ExtractedAppImage):

        if extraction.container_folder.query_exists():
            if extraction.container_folder.get_path().startswith(GLib.get_user_cache_dir()):
                shutil.rmtree(extraction.container_folder.get_path())

    def extract_appimage(self, file_path: str) -> ExtractedAppImage:
        file = Gio.File.new_for_path(file_path)

        desktop_entry: Optional[DesktopEntry.DesktopEntry] = None
        extraction_folder = None

        ## hash file
        temp_file = None

        with open(file.get_path(), 'rb') as f:
            temp_file = 'boutique_appimage_' + hashlib.md5(f.read()).hexdigest()

        folder = Gio.File.new_for_path(GLib.get_user_cache_dir() + f'/appimages/{temp_file}')

        if folder.query_exists():
            shutil.rmtree(folder.get_path())

        if folder.make_directory_with_parents(None):
            dest_file = Gio.File.new_for_path( folder.get_path() + f'/{temp_file}')
            file_copy = file.copy(
                dest_file, 
                Gio.FileCopyFlags.OVERWRITE, 
                None, None, None, None
            )

            dest_file_info = dest_file.query_info('*', Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS)

            if file_copy:
                squash_folder = Gio.File.new_for_path(f'{folder.get_path()}/squashfs-root')
                
                # set exec permission for dest_file
                # dest_file.set_attribute_string('unix::mode', '0755', Gio.FileQueryInfoFlags.NONE)
                os.chmod(dest_file.get_path(), 0o755)
                terminal.sh(["bash", "-c", f"cd {folder.get_path()} && {dest_file.get_path()} --appimage-extract "])

                if squash_folder.query_exists():
                    extraction_folder = squash_folder

                    desktop_file: Optional[Gio.File] = None
                    desktop_files: list[str] = filter(lambda x: x.endswith('.desktop'), os.listdir(f'{folder.get_path()}/squashfs-root'))

                    for d in desktop_files:
                        gdesk_file = Gio.File.new_for_path(f'{folder.get_path()}/squashfs-root/{d}')
                        if get_giofile_content_type(gdesk_file) == 'application/x-desktop':
                            desktop_file = gdesk_file
                            break

                    if desktop_file:
                        desktop_entry = DesktopEntry.DesktopEntry(desktop_file.get_path())
        
        result = ExtractedAppImage()
        result.desktop_entry = desktop_entry
        result.extraction_folder = extraction_folder
        result.container_folder = folder
        result.appimage_file = dest_file
        result.desktop_file = desktop_file

        return result

    def get_appimages_default_destination_path(self) -> str:
        return get_gsettings().get_string('appimages-default-folder').replace('~', GLib.get_home_dir())

    def get_previews(self, el):
        return []