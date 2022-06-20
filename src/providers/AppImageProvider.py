import random
import string
import threading
import logging
import urllib
import re
import os
import time
import requests
import html2text
import subprocess

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
        default_folder_path = get_gsettings().get_string('appimages-default-folder')
        
        try:
            folder = Gio.File.new_for_path(default_folder_path)
            desktop_files_dir = f'{GLib.get_home_dir()}/.local/share/applications/'
            for file_name in os.listdir(desktop_files_dir):
                gfile = Gio.File.new_for_path(desktop_files_dir + f'/{file_name}')

                try:
                    if get_giofile_content_type(gfile) == 'application/x-desktop':
                        f, _ = gfile.load_bytes(None)
                        print(f.get_data().decode('utf-8'))

                except Exception as e:
                    logging.warn(e)

        except Exception as e:
            logging.error(e)

        return []

    def is_installed(self, el: AppListElement, alt_sources: list[AppListElement]=[]) -> tuple[bool, AppListElement]:
        return (False, el)

    def get_icon(self, AppListElement, repo: str=None, load_from_network: bool=False) -> Gtk.Image:
        return Gtk.Image(resource="/it/mijorus/boutique/assets/flathub-badge-logo.svg")

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
            temp_file = 'temp_appimage_' + str(time.time_ns().__floor__())
            file = Gio.File.new_for_path(list_element.extra_data['file_path'])
            folder = Gio.File.new_for_path(GLib.get_user_cache_dir() + f'/appimages/{temp_file}')

            if folder.make_directory_with_parents(None):
                dest_file = Gio.File.new_for_path( folder.get_path() + f'/{temp_file}')
                file_copy = file.copy(
                    dest_file, 
                    Gio.FileCopyFlags.OVERWRITE, 
                    None, None, None, None
                )

                dest_file_info = dest_file.query_info('*', Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS)

                if file_copy:
                    terminal.sh(["bash", "-c", f"cd {folder.get_path()} && {dest_file.get_path()} --appimage-extract "])

                    squash_folder = Gio.File.new_for_path(f'{folder.get_path()}/squashfs-root')
                    if squash_folder.query_exists():
                        desktop_file: Optional[Gio.File] = None
                        desktop_files: list[str] = filter(lambda x: x.endswith('.desktop'), os.listdir(f'{folder.get_path()}/squashfs-root'))

                        for d in desktop_files:
                            gdesk_file = Gio.File.new_for_path(f'{folder.get_path()}/squashfs-root/{d}')
                            if get_giofile_content_type(gdesk_file) == 'application/x-desktop':
                                desktop_file = gdesk_file
                                break

                        if desktop_file:
                            # Move .appimage to its default location
                            appimages_destination_path = GLib.get_home_dir() + '/AppImages'
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
            else:
                callback(False)

        threading.Thread(target=install_job, daemon=True).start()
        return True

    def create_list_element_from_file(self, file: Gio.File) -> AppListElement:
        return AppListElement('test', 'test', 'test', 'appimage', InstalledStatus.NOT_INSTALLED,
            file_path=file.get_path()
        )

    def get_selected_source(self, list_element: list[AppListElement], source_id: str) -> AppListElement:
        pass

    def get_source_details(self, list_element: AppListElement) -> tuple[str, str]:
        pass
    
    def set_refresh_installed_status_callback(self, callback: Optional[Callable]):
        pass