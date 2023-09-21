import os
import subprocess

from setup import get_launch_script_path

if __name__ == '__main__':
    direwolf_dir = os.path.dirname(get_launch_script_path())
    os.chdir(direwolf_dir)
    subprocess.check_call(['direwolf.exe'])