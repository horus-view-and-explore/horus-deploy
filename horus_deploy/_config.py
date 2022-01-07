# Copyright (C) 2021-2022 Horus View and Explore B.V.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import configparser
import os
from pathlib import Path

import click


def _resolve_config_path():
    app_name = "horus"
    if os.name == "nt":
        app_name = "Horus View and Explore"

    path = Path(click.get_app_dir(app_name)) / "horus_deploy"

    if not path.exists():
        path.mkdir(parents=True)

    return path


def load_user_settings():
    settings = configparser.ConfigParser()
    if _SETTINGS_PATH.exists():
        settings.read(_SETTINGS_PATH)
    return settings


def user_config_dir():
    return _PATH


_PATH = _resolve_config_path()
_SETTINGS_PATH = _PATH / "settings.ini"
