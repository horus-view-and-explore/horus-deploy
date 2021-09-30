import pytest
from horus_deploy.operations.package import _get_name_from_rpm_path


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            "/yocto/yocto-configurations/nvidia/jetson-nano/jetson-nano-devkit/deploy/rpm/aarch64/htop-2.2.0-r0.aarch64.rpm",  # noqa: E501
            "htop",
        ),
        (
            "htop-2.2.0-r0.aarch64.rpm",
            "htop",
        ),
        (
            "python3-markupsafe-1.1.1-10.fc34.x86_64.rpm",
            "python3-markupsafe",
        ),
        (
            "this-is-not-correct",
            None,
        ),
        (
            "this-is-not-correct.rpm",
            None,
        ),
    ],
)
def test_get_name_from_rpm_path(test_input, expected):
    assert _get_name_from_rpm_path(test_input) == expected
