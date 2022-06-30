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
from xdg import DesktopEntry

from ..lib import flatpak, terminal
from ..lib.utils import log, cleanhtml, key_in_dict, gtk_image_from_url, qq, get_application_window, get_giofile_content_type, get_gsettings
from ..models.AppListElement import AppListElement, InstalledStatus
from ..components.CustomComponents import LabelStart
from ..models.Provider import Provider
from ..models.Models import FlatpakHistoryElement, AppUpdateElement
from typing import List, Callable, Union, Dict, Optional, List
from gi.repository import GLib, Gtk, Gdk, GdkPixbuf, Gio, GObject

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
                                file_path=gfile.get_path(),
                                provider='appimage'
                            ))

                except Exception as e:
                    logging.warn(e)

        except Exception as e:
            logging.error(e)

        return output

    def is_installed(self, el: AppListElement, alt_sources: list[AppListElement]=[]) -> tuple[bool, AppListElement]:
        return (False, el)

    def get_icon(self, el: AppListElement, repo: str=None, load_from_network: bool=False) -> Gtk.Image:
        icon_path = get_gsettings().get_string('appimages-default-folder').replace('~', GLib.get_home_dir()) + '/' + el.id + '.png'

        if os.path.exists(icon_path):
            Gtk.Image.new_from_file(icon_path)
        else:
            return Gtk.Image(resource="/it/mijorus/boutique/assets/App-image-logo-bw.svg")

    def uninstall(self, el: AppListElement, c: Callable[[bool], None]):
        pass

    def install(self, el: AppListElement, c: Callable[[bool], None]):
        pass

    def search(self, query: str) -> List[AppListElement]:
        return []

    def get_long_description(self, el: AppListElement) ->  str:
        return ''

    def load_extra_data_in_appdetails(self, widget: Gtk.Widget, el: AppListElement):
        pass

    def list_updatables(self) -> List[AppUpdateElement]:
        return []

    def update(self, el: AppListElement, callback: Callable[[bool], None]):
        pass
    
    def update_all(self, callback: Callable[[bool, str, bool], None]):
        pass

    def updates_need_refresh(self) -> bool:
        return False

    def run(self, el: AppListElement):
        pass

    def can_install_file(self, file: Gio.File) -> bool:
        return get_giofile_content_type(file) == 'application/vnd.appimage'

    def is_updatable(self, app_id: str) -> bool:
        pass

    def install_file(self, list_element: AppListElement, callback: Callable[[bool], None]) -> bool:
        def install_job():
            list_element.installed_status = InstalledStatus.INSTALLING

            try:
                desktop_entry, extraction_folder, dest_file, desktop_file = self.extract_appimage(file_path=list_element.extra_data['file_path'])
                dest_file_info = dest_file.query_info('*', Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS)

                if extraction_folder.query_exists():
                    # Move .appimage to its default location
                    appimages_destination_path = self.get_appimages_default_destination_path()
                    if dest_file.move(
                        Gio.File.new_for_path(appimages_destination_path + '/' + dest_file_info.get_name()), 
                        Gio.FileCopyFlags.OVERWRITE, 
                        None, None, None, None
                    ):
                        log(f'file moved to {appimages_destination_path}')

                        # Move .desktop file to its default location
                        desktop_files_destination_path = GLib.get_home_dir() + '/.local/share/applications'
                        if desktop_file.move(
                            Gio.File.new_for_path(f'{desktop_files_destination_path}/{dest_file_info.get_name()}.desktop'), 
                            Gio.FileCopyFlags.OVERWRITE, 
                            None, None, None, None
                        ):
                        
                            log('desktop file moved to ' + desktop_files_destination_path)
                            list_element.installed_status = InstalledStatus.INSTALLED

            except Exception as e:
                logging.error(e)
                list_element.installed_status = InstalledStatus.ERROR

            finally:
                self.post_file_extraction_cleanup(extraction_folder)
                callback(list_element.installed_status == InstalledStatus.INSTALLED)


        threading.Thread(target=install_job, daemon=True).start()
        return True

    def create_list_element_from_file(self, file: Gio.File) -> AppListElement:
        desktop_entry, extraction_folder, dest_file, desktop_file = self.extract_appimage(file_path=file.get_path())
        self.post_file_extraction_cleanup(extraction_folder)

        return AppListElement(
            name=desktop_entry.getName(), 
            description=desktop_entry.getComment(), 
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

    def post_file_extraction_cleanup(self, squash_folder: Gio.File):
        if squash_folder.query_exists() and squash_folder.get_path().startswith(GLib.get_user_cache_dir()):
            shutil.rmtree(squash_folder.get_path())

    def extract_appimage(self, file_path: str) -> tuple[DesktopEntry.DesktopEntry, Gio.File, Gio.File, Gio.File]:
        file = Gio.File.new_for_path(file_path)

        desktop_entry = None
        extraction_folder = None

        ## hash file
        temp_file = 'boutique_appimage_' + hashlib.md5(open(file.get_path(), 'rb').read()).hexdigest()
        folder = Gio.File.new_for_path(GLib.get_user_cache_dir() + f'/appimages/{temp_file}')

        self.post_file_extraction_cleanup(folder)

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
        
        return desktop_entry, extraction_folder, dest_file, desktop_file

    def get_appimages_default_destination_path(self) -> str:
        return get_gsettings().get_string('appimages-default-folder').replace('~', GLib.get_home_dir())