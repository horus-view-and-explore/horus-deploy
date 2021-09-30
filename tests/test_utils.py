from pathlib import Path

import click
import pytest
from click.testing import CliRunner
from horus_deploy.utils import (
    AttrDict,
    interpret_value,
    IdentifierOrKeyValue,
    multi_choice_prompt,
    single_choice_prompt,
    temp_python_files,
)


def test_attrdict():
    d = AttrDict()
    d.a = 1
    assert "a" in d
    d["b"] = 1
    assert "b" in d
    d.c = {"x": 2}
    assert d.c.x == 2


def test_attrdict_missing_attr():
    d = AttrDict()

    with pytest.raises(AttributeError):
        d.a


def test_temp_python_files():
    with temp_python_files("hello.py", "planet/world.py") as (fd1, fd2):
        py1 = Path(fd1.name)
        py2 = Path(fd2.name)

        assert py1.name == "hello.py"
        assert py2.name == "world.py"
        assert py2.parent.name == "planet"

        assert py1.exists()
        assert py2.exists()

    # After the with-statement block the files are deleted.
    assert not py1.exists()
    assert not py2.exists()


@pytest.mark.parametrize(
    "value,expected",
    [
        ("true", True),
        ("false", False),
        ("1337", 1337),
        ("3.14", 3.14),
        ("hello", "hello"),
        ("0xF00D", "0xF00D"),
    ],
)
def test_interpret_value(value, expected):
    assert interpret_value(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("abc", ("abc", None)),
        ("install_ssh_key", ("install_ssh_key", None)),
        ("website=https://horus.nu/", ("website", "https://horus.nu/")),
        ("website=", ("website", "")),
    ],
)
def test_IdentifierOrKeyValue(value, expected):
    obj = IdentifierOrKeyValue()
    assert obj.convert(value, None, None) == expected


def test_IdentifierOrKeyValue_bad_key():
    obj = IdentifierOrKeyValue()
    with pytest.raises(click.exceptions.BadParameter):
        obj.convert("@#$%^&*=1", None, None)


@pytest.mark.parametrize(
    "choices,output,expected",
    [
        ("1", ": 1\n", [1]),
        ("1    2", ": 1    2\n", [1, 2]),
        ("1 , , , 2", ": 1 , , , 2\n", [1, 2]),
        ("1 , , , 2 3", ": 1 , , , 2 3\n", [1, 2, 3]),
        ("4\n1", ": 4\nInvalid choice. Try again.\n: 1\n", [1]),
        ("a\n1", ": a\nInvalid choice. Try again.\n: 1\n", [1]),
    ],
)
def test_multi_choice_prompt(choices, output, expected):
    text = ""
    menu = [1, 2, 3]

    @click.command()
    def prompt():
        assert multi_choice_prompt(text, menu) == expected

    runner = CliRunner()
    result = runner.invoke(prompt, input=choices)
    assert not result.exception
    assert result.output == output


@pytest.mark.parametrize(
    "choice,output,expected",
    [
        ("1", ": 1\n", 1),
        ("a\n1", ": a\nInvalid choice. Try again.\n: 1\n", 1),
        ("4\n1", ": 4\nInvalid choice. Try again.\n: 1\n", 1),
    ],
)
def test_single_choice_prompt(choice, output, expected):
    text = ""
    menu = [1, 2, 3]

    @click.command()
    def prompt():
        assert single_choice_prompt(text, menu) == expected

    runner = CliRunner()
    result = runner.invoke(prompt, input=choice)
    assert not result.exception
    assert result.output == output
