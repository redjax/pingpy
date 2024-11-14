from __future__ import annotations

import os
from pathlib import Path

import pytest

@pytest.mark.sanity
def test_python_version(python_ver: str):
    assert python_ver, ValueError("python_ver should not be empty")
    assert isinstance(python_ver, str), TypeError(f"Invalid type for python_ver: ({type(python_ver)}). Expected: str")
    
    print(f"Python version: {python_ver}")