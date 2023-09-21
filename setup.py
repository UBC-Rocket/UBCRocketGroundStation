import os
import platform
import urllib.request
import zipfile
import shutil

#works for windows only
#complicated installation process for linux and mac users, for now install and run manually 

VERSION = '1.6'
DOWNLOAD_URL = f'https://github.com/wb2osz/direwolf/releases/download/{VERSION}/direwolf-1.6.0-413855e_x86_64.zip'
INSTALL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'direwolf')

def is_installed():
    return os.path.exists(get_launch_script_path())

def download_and_extract():
    os.makedirs(INSTALL_DIR, exist_ok=True)
    filename, headers = urllib.request.urlretrieve(DOWNLOAD_URL)
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(INSTALL_DIR)

def get_launch_script_path():
    system = platform.system()
    if system == 'Windows':
        return os.path.join(INSTALL_DIR, 'direwolf-1.6.0-413855e_x86_64', 'direwolf.exe')
    # elif system == 'Linux':
    #     return os.path.join(INSTALL_DIR, f'direwolf-{VERSION}', 'direwolf')
    # elif system == 'Darwin':
    #     return os.path.join(INSTALL_DIR, f'direwolf-{VERSION}', 'direwolf')
    else:
        raise OSError(f'Unsupported platform (only compatible with windows for now): {system}')

if __name__ == '__main__':
    if is_installed():
        print('Direwolf is already installed.')
    else:
        download_and_extract()
        print('Direwolf installation complete.') 