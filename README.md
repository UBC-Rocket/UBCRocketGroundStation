# UBCRocketGroundStation
Absolutely flawless ground station code

Python 3.7.X is required.

If running pyenv on Linux, run `env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.7.0 && pyenv local 3.7.0`.

If running pyenv on MacOS, run `env PYTHON_CONFIGURE_OPTS="--enable-framework CC=clang" pyenv install 3.7.3 && pyenv local 3.7.3`.

Run `python build.py --skip test` to setup virtual environment, download dependencies, and build standalone executable.
