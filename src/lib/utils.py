import re
import os
import requests

from gi.repository import Gtk, Adw, GdkPixbuf, GLib

def key_in_dict(_dict: dict, key_lookup: str, separator='.'):
    """
        Searches for a nested key in a dictionary and returns its value, or None if nothing was found.
        key_lookup must be a string where each key is deparated by a given "separator" character, which by default is a dot
    """
    keys = key_lookup.split(separator)
    subdict = _dict

    for k in keys:
        if isinstance(subdict, dict):
            subdict = subdict[k] if (k in subdict) else None

        if subdict is None: break

    return subdict

def log(s):
    if os.getenv('DEBUG_MODE', None) == 'dev':
        print(s)

def add_page_to_adw_stack(stack: Adw.ViewStack, page: Gtk.Widget, name: str, title: str, icon: str):
    stack.add_titled( page, name, title )
    stack.get_page(page).set_icon_name(icon)

# as per recommendation from @freylis, compile once only
_html_clearner = None
def cleanhtml(raw_html: str) -> str:
    global _html_clearner

    if not _html_clearner:
        _html_clearner = re.compile('<.*?>')

    cleantext = re.sub(_html_clearner, '', raw_html)
    return cleantext

def gtk_image_from_url(url: str, image: Gtk.Image):
    response = requests.get(url)
    response.raise_for_status()

    loader = GdkPixbuf.PixbufLoader()
    loader.write_bytes(GLib.Bytes.new(response.content))
    loader.close()

    image.set_from_pixbuf(loader.get_pixbuf())