import pytest

from horus_deploy.metadata import extract_metadata


def test_metadata_as_int():
    data = "METADATA = 1"

    with pytest.raises(TypeError):
        extract_metadata(data)


def test_metadata_as_dict():
    data = "METADATA = {}"
    assert extract_metadata(data) == {}


def test_metadata_as_dict_with_value():
    data = "METADATA = {'id': 'test'}"
    expected = {"id": "test"}
    assert extract_metadata(data) == expected


def test_metadata_as_dict_with_value_from_variable():
    data = """\
s = 'test'
METADATA = {'id': s}
"""
    with pytest.raises(ValueError):
        extract_metadata(data)
