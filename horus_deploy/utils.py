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

import dataclasses
import json
import re
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Union, Callable, List

import click


class AttrDict(dict):
    def __getattr__(self, key):
        try:
            value = self.__getitem__(key)
            if value.__class__ != self.__class__ and value.__class__ == dict:
                self[key] = value = self.__class__(value)
            return value
        except KeyError:
            raise AttributeError(f"{key} not in {self.keys()}")

    def __setattr__(self, key, value):
        self.__setitem__(key, value)


@contextmanager
def temp_python_files(*files):
    with TemporaryDirectory() as dirname:
        fds = []

        for f in files:
            f = Path(dirname) / f
            if not f.parent.exists():
                f.parent.mkdir(0o700, parents=True)
            fds.append(f.open("w"))

        try:
            yield fds
        finally:
            for fd in fds:
                fd.close()


def multi_choice_prompt(text, menu):
    def _parse_choice(v):
        return list(map(int, re.split("[, ]+", v)))

    while True:
        try:
            choices = click.prompt(text, type=str, value_proc=_parse_choice)
            if not all(0 < c < (len(menu) + 1) for c in choices):
                raise ValueError
        except ValueError:
            click.echo("Invalid choice. Try again.")
        else:
            break

    items = [menu[i - 1] for i in choices]

    return items


def single_choice_prompt(text, menu):
    while True:
        try:
            choice = click.prompt(text, type=str)
            choice = int(choice)
            if not (0 < choice < (len(menu) + 1)):
                raise ValueError
        except ValueError:
            click.echo("Invalid choice. Try again.")
        else:
            break

    item = menu[choice - 1]

    return item


def interpret_value(v: str) -> Union[bool, int, float, str]:
    def to_bool(v):
        if v in ("true", "false"):
            return v == "true"
        raise ValueError

    types: List[Callable] = [
        to_bool,
        int,
        float,
    ]

    for typ in types:
        try:
            v = typ(v)
            break
        except ValueError:
            pass

    return v


class IdentifierOrKeyValue(click.ParamType):
    """Interpret parameters as key-value pairs or paths.

    E.g. "a=1" and "b=" both are interpret as key-value pairs.
    And "abc" and "install_ssh_key" are interpret as a path.
    """

    name = "ident-or-key-value"

    def convert(self, value, param, ctx):
        pair = value.split("=", 1)
        value = None

        if len(pair) == 2:
            key, value = pair
            value = interpret_value(value)
        else:
            key = pair[0]
        if not key.isidentifier():
            self.fail(f"{key!r} is not a valid identifier", param, ctx)

        return (key, value)


def json_dumps(obj):
    return json.dumps(obj, cls=JSONEncoder)


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return super().default(obj)
