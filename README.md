# UBCRocketGroundStation 
[![Build Status](https://circleci.com/gh/UBC-Rocket/UBCRocketGroundStation.svg?style=shield)](https://app.circleci.com/pipelines/github/UBC-Rocket/UBCRocketGroundStation)

Absolutely flawless ground station code.

Python 3.7.X is required.

If Python 3.7.X is not avaiable from your system's package repo, use pyenv along with the following:

* Linux:
    ```
    env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.7.9 && pyenv local 3.7.9
    ```

* MacOS: 
    ```
    env PYTHON_CONFIGURE_OPTS="--enable-framework CC=clang" pyenv install 3.7.9 && pyenv local 3.7.9
    ```

Run `python build.py --skip test` to setup virtual environment, download dependencies, and build standalone executable.
