# UBCRocketGroundStation 
[![Build Status](https://circleci.com/gh/UBC-Rocket/UBCRocketGroundStation.svg?style=shield)](https://app.circleci.com/pipelines/github/UBC-Rocket/UBCRocketGroundStation)
[![codecov](https://codecov.io/gh/UBC-Rocket/UBCRocketGroundStation/branch/master/graph/badge.svg?token=2IML1026UZ)](https://codecov.io/gh/UBC-Rocket/UBCRocketGroundStation)

Absolutely flawless ground station code.

Python 3.12.X is required.

If Python 3.12.X is not avaiable from your system's package repo, use pyenv along with the following:

* Linux:
    ```
    env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.12.6 && pyenv local 3.12.6
    ```

* MacOS: 
    ```
    env PYTHON_CONFIGURE_OPTS="--enable-framework CC=clang" pyenv install 3.12.6 && pyenv local 3.12.6
    ```

Run `python build.py --skip test` to setup virtual environment, download dependencies, and build standalone executable.
