#!/bin/sh
set -o errexit
set -o verbose


  #####################################
  #               SETUP               #
  #####################################

sudo apt-get update -y

# Needed for unit testing with qt https://github.com/pytest-dev/pytest-qt/issues/293
sudo apt-get install -y xvfb libxkbcommon-x11-0
sudo Xvfb :1 -screen 0 1024x768x24 </dev/null &
export DISPLAY=":1"

# Setup JDK for OpenRocket
sudo apt-get install -y openjdk-8-jre
export JAVA_HOME="/usr/lib/jvm/java-8-openjdk-amd64"

# Start setting up Python for GS
sudo apt-get install -y tk-dev
env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.7.9
pyenv global 3.7.9
python --version
python -m pip install --upgrade pip setuptools wheel

# Initial setup of GS and venv
echo "$MAPBOX_API_KEY" > apikey.txt
python build.py --only setup
cd ..

# Clone and build FW for SIM based integration tests
git clone https://github.com/UBC-Rocket/FLARE.git
mkdir FLARE/avionics/build
cd FLARE/avionics/build
cat ../../../UBCRocketGroundStation/required_flare.txt | xargs git checkout
cmake ..
cmake --build . -j 2
cd ../../..


  #####################################
  #               TEST                #
  #####################################

cd UBCRocketGroundStation

# Unit tests & integration tests
source venv/bin/activate
mkdir test_reports

# Unit
coverage run --omit 'venv/*' -m pytest --durations=0 --junitxml=test_reports/unit-test-results.xml --ignore=tests/integration_tests tests
coverage report --omit 'venv/*'
coverage xml -o test_reports/unit-test-coverage.xml
head test_reports/unit-test-coverage.xml

# Integration
coverage run --omit 'venv/*' -m pytest --durations=0 --junitxml=test_reports/integ-test-results.xml tests/integration_tests
coverage report --omit 'venv/*'
coverage xml -o test_reports/integ-test-coverage.xml
head test_reports/integ-test-coverage.xml

deactivate

# Pyinstaller "build" test & GS self-test
python build.py --skip setup
