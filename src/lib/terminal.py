import subprocess

def _command_is_allowed(command: str) -> bool:
    allowed = ['flatpak']
    return command.split(' ')[0] in allowed

def sh(command: str) -> str:
    if not _command_is_allowed(command):
        raise Exception('Running this command is not allowed. The number available commands is restricted for security reasons')

    try:
        output = subprocess.run([f'flatpak-spawn --host {command}'], encoding='utf-8', shell=True, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        raise Exception(e.stderr) from e

    return output.stdout