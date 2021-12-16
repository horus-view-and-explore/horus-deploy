import os
from pathlib import Path

from pyinfra.operations import server, files

METADATA = {
    "name": "Diagnostics",
    "description": (
        "Gather diagnostics from host and download to current "
        "directory as diagnostics.tar.gz."
    )
}

SOURCE = "/data/diagnostics.tar.gz"
TARGET = Path(os.getcwd()) / "diagnostics.tar.gz"

server.shell(["create_diagnostics"])

files.get(
    src=SOURCE,
    dest=TARGET,
)
