from pathlib import Path
from unittest.mock import patch

from horus_deploy import deploys

SCRIPT_BASE_PATH = Path(__file__).parent / "testdata" / "deploy_scripts"
BUILTIN_SCRIPTS = SCRIPT_BASE_PATH / "builtin"
USER_SCRIPTS = SCRIPT_BASE_PATH / "user"
LOCAL_SCRIPTS = SCRIPT_BASE_PATH / "local"


@patch("horus_deploy.deploys._BUILTIN", BUILTIN_SCRIPTS)
@patch("horus_deploy.deploys._USER_DIR", USER_SCRIPTS)
@patch("horus_deploy.deploys.Path.cwd")
def test_find_deploy_scripts(path_cwd):
    path_cwd.return_value = LOCAL_SCRIPTS

    expected_result = [
        {
            "name": "a",
            "id": "a",
            "path": BUILTIN_SCRIPTS / "a.py",
            "type": deploys.Type.BUILTIN,
        },
        {
            "name": "b",
            "id": "b",
            "path": USER_SCRIPTS / "b" / "deploy.py",
            "type": deploys.Type.USER,
        },
        {
            "name": "c",
            "id": "c",
            "path": LOCAL_SCRIPTS / "c.py",
            "type": deploys.Type.LOCAL,
        },
    ]
    actual_result = deploys.find_deploy_scripts()

    assert actual_result == expected_result


@patch("horus_deploy.deploys._BUILTIN", BUILTIN_SCRIPTS)
@patch("horus_deploy.deploys._USER_DIR", USER_SCRIPTS)
@patch("horus_deploy.deploys.Path.cwd")
def test_find_deploy_scripts_with_filter(path_cwd):
    path_cwd.return_value = LOCAL_SCRIPTS

    expected_result = [
        {
            "name": "a",
            "id": "a",
            "path": BUILTIN_SCRIPTS / "a.py",
            "type": deploys.Type.BUILTIN,
        },
    ]
    actual_result = deploys.find_deploy_scripts("a")

    assert actual_result == expected_result


def test_is_relative_to():
    assert deploys.is_relative_to(Path("/home/root"), "/home")


def test_is_not_relative_to():
    assert not deploys.is_relative_to(Path("/usr/lib"), "/home")
