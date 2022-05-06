import subprocess
import re
import asyncio
import threading
from typing import Callable, List, Union
from .utils import log

def _command_is_allowed(command: str) -> bool:
    allowed = ['flatpak']
    return command.split(' ')[0] in allowed

_sanitizer = None
def sanitize(_input: str) -> str:
    global _sanitizer

    if not _sanitizer:
        _sanitizer = re.compile(r'[^0-9a-zA-Z]+')

    return re.sub(_sanitizer, " ", _input)

def sh(command: Union[str, List[str]], hide_err=False) -> str:
    to_check = command if isinstance(command, str) else command[0]
    if not _command_is_allowed(to_check):
        raise Exception('Running this command is not allowed. The number available commands is restricted for security reasons')

    try:
        log(f'Running {command}')

        cmd = f'flatpak-spawn --host {command}'.split(' ') if isinstance(command, str) else ['flatpak-spawn', '--host', *command]
        output = subprocess.run(cmd, encoding='utf-8', shell=False, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        if not hide_err: print(e.stderr)
        raise Exception(e.stderr) from e

    return re.sub(r'\n$', '', output.stdout)

def threaded_sh(command: str, callback: Callable[[str], None]=None):
    if not _command_is_allowed(command):
        raise Exception('Running this command is not allowed. The number available commands is restricted for security reasons')

    
    def run_command(command: str, callback: Callable[[str], None]=None):
        try:
            log(f'Running {command}')

            cmd = f'flatpak-spawn --host {command}'.split(' ')
            output = subprocess.run(cmd, encoding='utf-8', shell=False, check=True, capture_output=True)

            if callback:
                callback(re.sub(r'\n$', '', output.stdout))

        except subprocess.CalledProcessError as e:
            log(e.stderr)
            raise Exception(e.stderr) from e

    thread = threading.Thread(target=run_command, daemon=True, args=(command, callback, ))
    thread.start()