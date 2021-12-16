{ pkgs }:
with pkgs; python3Packages.buildPythonApplication rec {
  pname = "pyinfra";
  version = "1.5";

  src = python3Packages.fetchPypi {
    inherit pname version;
    sha256 = "sha256-MeKMo5J9r7gYQFvwBhum6MmM7zBD8VVpKVk9rrLJRlI=";
  };

  propagatedBuildInputs = with python3Packages; [
    gevent
    paramiko
    configparser
    click
    colorama
    python-dateutil
    jinja2
    six
    setuptools
    pywinrm
    distro
  ];

  disabledTestPaths = [
    "tests/test_facts.py"
  ];

  disabledTests = [
    "test_get_fact"
    "test_deploy"
    "test_interdependent_deploy"
    "test_legacy_deploy"
    "test_user_op"
    "test_make_names_data_ini"
    "test_make_names_data_json"
    "test_make_names_data_yaml"
    "test_load_ssh_config"
  ];

  checkInputs = with python3Packages; [
    pytestCheckHook
    mock
    coverage
    codecov
    pyyaml
  ];
}
