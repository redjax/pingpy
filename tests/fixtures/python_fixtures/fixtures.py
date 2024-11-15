from __future__ import annotations

import platform
import typing as t

from pytest import fixture

@fixture
def sandbox_dir(fs):
    ## Add templates directory to the fake filesystem
    fs.add_real_directory("t", lazy_read=False)

    sandbox = fs.create_dir("/sandbox")

    return sandbox

@fixture
def python_ver() -> str:
    return platform.python_version()