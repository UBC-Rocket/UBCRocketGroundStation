#!/bin/sh
set -o nounset
set -o errexit
set -o xtrace


  #####################################
  #               SETUP               #
  #####################################

# Needed for unit testing with qt https://github.com/pytest-dev/pytest-qt/issues/293
sudo apt-get install -y xvfb libxkbcommon-x11-0
sudo Xvfb :1 -screen 0 1024x768x24 </dev/null &
export DISPLAY=":1"

# Start setting up environment for GS
sudo apt-get install -y python3.7 python3-pip python3.7-venv python3-tk libpython3.7-dev
python3.7 -m pip install --upgrade pip setuptools wheel
python3.7 --version

# Initial setup of GS and venv
git clone https://github.com/UBC-Rocket/UBCRocketGroundStation.git --recurse-submodules
cd UBCRocketGroundStation
echo "$MAPBOX_API_KEY" > apikey.txt
python3.7 build.py --only setup
cd ..

# Clone and build FW for SIM based integration tests
git clone https://github.com/UBC-Rocket/FLARE.git --recurse-submodules
mkdir FLARE/avionics/build
cd FLARE/avionics/build
cat ../../../UBCRocketGroundStation/required_flare.txt | xargs git checkout
cmake ..
cmake --build .
cd ../../..


  #####################################
  #               TEST                #
  #####################################

cd UBCRocketGroundStation

# Unit tests & integration tests
source venv/bin/activate
python -m pytest
deactivate

# Pyinstaller "build" test & GS self-test
python3.7 build.py --skip setup
