import os

project_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(project_dir)

has_existing_init_dir = os.path.isfile('__init__.py')

if not has_existing_init_dir:
    open('__init__.py', 'x')

# graphviz must be installed on your computer, with the bin file added to PATH
# https://graphviz.org/download
os.system('pyreverse -o png -p UBCROCKETGROUNDSTATION .')

if not has_existing_init_dir:
    os.remove('__init__.py')