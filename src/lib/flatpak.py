from typing import List
from .terminal import sh

def list_() -> List:
    headers: List[str] = ['name', 'description', 'application', 'version', 'branch', 'arch', 'runtime', 'origin', 'installation', 'ref', 'active', 'latest', 'size']
    output_list: str = sh(f'flatpak list --columns={",".join(headers)}')

    output: List = []
    for row in output_list.split('\n'):
        if not '\t' in row:
            break

        columns: List[str] = row.split('\t')

        app_details = {}
        for col, h in zip(columns, headers):
            app_details[h] = col

        output.append(app_details)

    return output
