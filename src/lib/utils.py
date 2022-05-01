import os
from gi.repository import Gtk, Adw

def key_in_dict(_dict: dict, key_lookup: str, separator='.'):
    """
        Searches for a nested key in a dictionary and returns its value, or None if nothing was found.
        key_lookup must be a string where each key is deparated by a given "separator" character, which by default is a dot
    """
    keys = key_lookup.split(separator)
    subdict = _dict

    for k in keys:
        subdict = subdict[k] if k in subdict else None
        if subdict is None: break

    return subdict

def log(s: str):
    if os.getenv('DEBUG_MODE', None) == 'dev':
        print(s)

def add_page_to_adw_stack(stack: Adw.ViewStack, page: Gtk.Widget, name: str, title: str, icon: str):
    stack.add_titled( page, name, title )
    stack.get_page(page).set_icon_name('icon')
