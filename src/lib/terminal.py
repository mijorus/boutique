import subprocess
import re
import asyncio
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

def async_sh(command: str, callback: Callable[[str], None]):
    if not _command_is_allowed(command):
        raise Exception('Running this command is not allowed. The number available commands is restricted for security reasons')

    try:
        print(f'Running {command}')
        cmd = f'flatpak-spawn --host {command}'.split(' ')
        proc = subprocess.Popen(cmd, stdout=asyncio.subprocess.PIPE)
        proc.wait(2)
        out, err = proc.communicate()

        output = out.decode('utf-8')
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        raise Exception(e.stderr) from e

    #     proc = await asyncio.create_subprocess_exec(
    #         'flatpak-spawn', 
    #         '--host', 
    #         *cmd,
    #         stdout=asyncio.subprocess.PIPE,
    #         stderr=asyncio.subprocess.PIPE
    #     )

    #     output, stderr = await proc.communicate()

    #     if stderr:
    #         raise Exception()

    # except Exception as e:
    #     print(e)
    #     raise Exception(e) from e

    callable(output)