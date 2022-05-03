import re
from typing import List, Callable, Dict, Union
from .terminal import sh, threaded_sh, sanitize
from ..models.AppsListSection import AppsListSection
from .utils import key_in_dict, log

_columns_query: List[str] = ['name', 'description', 'application', 'version', 'branch', 'arch', 'runtime', 'origin', 'installation', 'ref', 'active', 'latest', 'size']

def _parse_output(command_output: str, headers: List[str], to_sort=True) -> List[Dict]:
    output: List = []
    for row in command_output.split('\n'):
        if not '\t' in row:
            break

        columns: List[str] = row.split('\t')

        app_details = {}
        for col, h in zip(columns, headers):
            app_details[h] = col

        output.append(app_details)

    if to_sort:
        output = sorted(output, key=lambda o: o['name'].lower())

    return output

def full_list() -> List:
    output_list: str = sh(f'flatpak list --user --columns={",".join(_columns_query)}')

    output: List = _parse_output(output_list, _columns_query)
    return output

def apps_list() -> List:
    output_list: str = sh(f'flatpak list --app --columns={",".join(_columns_query)}')

    output: List = _parse_output(output_list, _columns_query)
    return output

def libs_list() -> List:
    output_list: str = sh(f'flatpak list --runtime --columns={",".join(_columns_query)}')

    output: List = _parse_output(output_list, _columns_query)
    return output

def sectioned_list() -> List[AppsListSection]:
    output: List[AppsListSection] = [
        AppsListSection('installed', apps_list()),
        AppsListSection('libraries', libs_list())
    ]

    return output

def get_default_aarch() -> str:
    return sh('flatpak --default-arch')

def get_ref_origin(ref: str) -> str:
    return sh(f'flatpak info {ref} -o')

def remove(ref: str, kill_id: str=None, callback: Callable=None):
    if kill_id:
        try:
            sh(f'flatpak kill {kill_id}')
        except Exception as e:
            pass

    threaded_sh(f'flatpak remove {ref} --user -y --no-related', callback)

def install(repo: str, app_id: str):
    sh(f'flatpak install --user -y {repo} {app_id}')

def search(query: str) -> List[Dict]: 
    query = query.strip()
    query = sanitize(query)

    cols = ['name', 'description', 'application', 'version', 'branch', 'remotes']
    res = sh(['flatpak', 'search', '--user', f'--columns={",".join(cols)}', *query.split(' ')])

    return _parse_output(res, cols, to_sort=False)

_cached_remotes: Union[Dict['str', Dict], None] = None
def remotes_list(cache=True) -> Dict['str', Dict]:
    global _cached_remotes

    if _cached_remotes and cache:
        return _cached_remotes

    cols = [ 'name','title','url','collection','subset','filter','priority','options','comment','description','homepage','icon' ]
    result = _parse_output(sh(f'flatpak remotes --user --columns={",".join(cols)}'), cols, False)

    output = {}
    for r in result:
        output[r['name']] = r
        del output[r['name']]['name']
    
    _cached_remotes = output
    return output

def is_installed(app_id: str) -> bool:
    for i in apps_list():
        if i['application'] == app_id:
            return True

    return False