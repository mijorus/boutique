import os

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