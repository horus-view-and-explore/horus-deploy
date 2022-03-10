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

import ast
from typing import Dict, List, Any


_VARIABLE_NAME = "METADATA"


def extract_metadata(source_code: str) -> Dict:
    """Extract metadata from deploy script.

    I.e. the value of a top-level variable named METADATA is extracted
    from Python source code.
    """
    module = ast.parse(source_code)
    metadata = {}

    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue

        names = _get_names_from_targets(node.targets)
        if _VARIABLE_NAME in names:
            if not isinstance(node.value, ast.Dict):
                raise TypeError(f"{_VARIABLE_NAME} value must be a dict")
            metadata = ast.literal_eval(node.value)
            break

    return metadata


def _get_names_from_targets(targets: List[Any]) -> List[str]:
    names = []

    for target in targets:
        if isinstance(target, ast.Name):
            names.append(target.id)
        elif isinstance(target, ast.Tuple):
            names.extend(_get_names_from_targets(target.elts))
        else:
            raise TypeError(f"don't know how to get name from {target}")

    return names
