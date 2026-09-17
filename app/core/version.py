#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""The running application's version.

Read from pyproject.toml rather than duplicated in a __version__ constant,
so a release bump happens in one place.  importlib.metadata is not usable
here: the project is run from its source tree and never pip-installed, so it
has no package metadata to read.
"""
# -----------------------------------------------------------------------------

import tomllib

from functools import lru_cache
from pathlib import Path


# -----------------------------------------------------------------------------

_PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


# -----------------------------------------------------------------------------

@lru_cache
def app_version() -> str:
    """The version from pyproject.toml, prefixed with v.

    instance_metadata constrains its version columns to ^v\\d+\\.\\d+\\.\\d+$,
    so the prefix is part of the format rather than decoration.
    """
    with _PYPROJECT.open("rb") as fh:
        return "v" + tomllib.load(fh)["project"]["version"]


# -----------------------------------------------------------------------------
