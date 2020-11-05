import argparse
import sys
import os
import subprocess
from collections import OrderedDict

'''
PyInstaller settings
'''
EXECUTABLE_NAME = 'UBCRGS'

ENTRY_POINT = 'start.py'

DATA_FILES = [
    'qt_files/main.ui',
    'qt_files/marker.png',
    'qt_files/com_window.ui'
]

HIDDEN_IMPORTS = [
    'qt_files.mplwidget'
]

'''
Environment specific paths and constants
'''
LOCAL = os.path.dirname(os.path.abspath(__file__))

GLOBAL_PYTHON = sys.executable

VENV_BIN_DIR = os.path.join(LOCAL, {
    'linux': 'venv/bin/',
    'win32': 'venv/Scripts/',
    'darwin': 'venv/bin/'
}[sys.platform])

EXECUTABLE_FILE_EXTENSION = {
    'linux': '',
    'win32': '.exe',
    'darwin': ''
}[sys.platform]

VENV_PYTHON = os.path.join(VENV_BIN_DIR, {
    'linux': 'python3',
    'win32': 'python',
    'darwin': 'python3'
}[sys.platform] + EXECUTABLE_FILE_EXTENSION)

VENV_PIP = os.path.join(VENV_BIN_DIR, 'pip' + EXECUTABLE_FILE_EXTENSION)

VENV_PYINSTALLER = os.path.join(VENV_BIN_DIR, 'pyinstaller' + EXECUTABLE_FILE_EXTENSION)

BUILD_OUTPUT = os.path.join(LOCAL, 'dist/', EXECUTABLE_NAME + EXECUTABLE_FILE_EXTENSION)

PYINSTALLER_SEPARATOR = {
    'linux': ':',
    'win32': ';',
    'darwin': ':'
}[sys.platform]


def _run(executable, args):
    cmd = [executable] + args
    cmd = ' '.join(cmd)
    print(cmd)
    sys.stdout.flush() # Otherwise the output gets mixed with the subprocess output
    subprocess.run(cmd, cwd=LOCAL, check=True, shell=True)


def _is_venv():
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))


def setup_step():
    print("Creating venv...")

    _run(GLOBAL_PYTHON, ['-m', 'venv', 'venv'])

    print("Printing some venv debug info...")
    _run(VENV_PYTHON, ['--version'])
    _run(VENV_PYTHON, ['-c', '"import sys; print(sys.executable)"'])

    print("Installing requirements in venv...")
    _run(VENV_PIP, ['install', '-r', 'requirements.txt'])


def build_step():
    print("Running PyInstaller...")
    hidden_imports = [f"--hidden-import={i}" for i in HIDDEN_IMPORTS]
    data_files = [f"--add-data={i}{PYINSTALLER_SEPARATOR}{os.path.dirname(i)}" for i in DATA_FILES]
    _run(VENV_PYINSTALLER, ['-F', '-n', EXECUTABLE_NAME, ENTRY_POINT] + hidden_imports + data_files)


def test_step():
    print("Starting self-test...")
    _run(BUILD_OUTPUT, ['--self-test'])


BUILD_STEPS = OrderedDict({
    'setup': setup_step,
    'build': build_step,
    'test': test_step
})


def main(cmd_args):
    """
    Validate input
    """
    if cmd_args.only and cmd_args.skip:
        raise Exception("Cannot use --skip and --only together")

    if cmd_args.only or cmd_args.skip:
        for step in cmd_args.only if cmd_args.only else cmd_args.skip:
            if step not in BUILD_STEPS:
                raise Exception(f"Invalid build step: {step}")

    """
    Run build steps in order
    """
    for step in BUILD_STEPS.keys():
        if cmd_args.skip and step in cmd_args.skip:
            print(f"Skipping build step: {step}")
            continue
        elif cmd_args.only and step not in cmd_args.only:
            print(f"Skipping build step: {step}")
            continue
        else:
            print(f"Starting build step: {step}")
            BUILD_STEPS[step]()
            print(f"Finished build step: {step}")


if __name__ == '__main__':
    if not (sys.version_info[0] == 3 and sys.version_info[1] == 7):
        raise Exception("Python version is not 3.7")

    if _is_venv():
        raise Exception("Running in a virtual environment")

    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--skip", nargs='+', type=str,
                        help="List of build steps to skip. Cannot be used in conjunction with --only")
    parser.add_argument("-o", "--only", nargs='+', type=str,
                        help="List of build steps to run exclusively. Cannot be used in conjunction with --skip")

    cmd_args = parser.parse_args()

    main(cmd_args)
