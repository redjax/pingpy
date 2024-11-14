import typing as t
from pytest import fixture
import platform

@fixture
def sandbox_dir(fs):
    ## Add templates directory to the fake filesystem
    fs.add_real_directory("t", lazy_read=False)

    sandbox = fs.create_dir("/sandbox")

    return sandbox

@fixture
def python_ver() -> str:
    return platform.python_version()