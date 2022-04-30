import subprocess
import re
import asyncio
import threading
from typing import Callable

def _command_is_allowed(command: str) -> bool:
    allowed = ['flatpak']
    return command.split(' ')[0] in allowed

def sh(command: str) -> str:
    if not _command_is_allowed(command):
        raise Exception('Running this command is not allowed. The number available commands is restricted for security reasons')

    try:
        cmd = f'flatpak-spawn --host {command}'.split(' ')
        output = subprocess.run(cmd, encoding='utf-8', shell=False, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        raise Exception(e.stderr) from e

    return re.sub(r'\n$', '', output.stdout)

def threaded_sh(command: str, callback: Callable[[str], None]=None):
    if not _command_is_allowed(command):
        raise Exception('Running this command is not allowed. The number available commands is restricted for security reasons')

    
    def run_command():
        try:
            print(f'Running {command}')

            cmd = f'flatpak-spawn --host {command}'.split(' ')
            output = subprocess.run(cmd, encoding='utf-8', shell=False, check=True, capture_output=True)

            if callback:
                callback(re.sub(r'\n$', '', output.stdout))

        except subprocess.CalledProcessError as e:
            print(e.stderr)
            raise Exception(e.stderr) from e

    
    thread = threading.Thread(target=run_command, daemon=True)
    thread.start()