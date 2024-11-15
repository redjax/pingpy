from __future__ import annotations

from contextlib import contextmanager
import importlib.util
import logging
import os
from pathlib import Path
import platform
import shutil
import typing as t

import nox

## Set nox options
if importlib.util.find_spec("uv"):
    nox.options.default_venv_backend = "uv|virtualenv"
else:
    nox.options.default_venv_backend = "virtualenv"
nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_external_run = False
nox.options.error_on_missing_interpreters = False
# nox.options.report = True

## Define sessions to run when no session is specified
nox.sessions = ["lint", "export", "tests"]

## Create logger for this module
log: logging.Logger = logging.getLogger("nox")

## Define versions to test
PY_VERSIONS: list[str] = ["3.12", "3.11"]
## Get tuple of Python ver ('maj', 'min', 'mic')
PY_VER_TUPLE: tuple[str, str, str] = platform.python_version_tuple()
## Dynamically set Python version
DEFAULT_PYTHON: str = f"{PY_VER_TUPLE[0]}.{PY_VER_TUPLE[1]}"

## Set directory for requirements.txt file output
REQUIREMENTS_OUTPUT_DIR: Path = Path(".")

# this VENV_DIR constant specifies the name of the dir that the `dev`
# session will create, containing the virtualenv;
# the `resolve()` makes it portable
VENV_DIR = Path("./.venv").resolve()

LINT_PATHS: list[str] = ["src", "tests"]


def install_uv_project(session: nox.Session, external: bool = False) -> None:
    """Method to install uv and the current project in a nox session."""
    log.info("Installing uv in session")
    session.install("uv")
    log.info("Syncing uv project")
    session.run("uv", "sync", external=external)
    log.info("Installing project")
    session.run("uv", "pip", "install", ".", external=external)


def bump_project_version(session: nox.Session, bump_type: str = "patch", dry_run: bool = False):
    VALID_BUMP_TYPES = ["major", "minor", "patch"]
    
    session.install("bump-my-version")
    
    ## Check if arg was passed and validate
    if not bump_type or bump_type == "" or bump_type == " " or bump_type is None:
        raise ValueError("Missing a bump type {VALID_BUMP_TYPES}")
    
    if bump_type not in ["major", "minor", "patch"]:
        raise ValueError(f"Invalid bump type: '{bump_type}'. Must be one of: {VALID_BUMP_TYPES}")
    
    match bump_type:
        case "major":
            log.info("Bumping major version")
            
            if dry_run:
                session.log("Dry run enabled, no version bump will occur")
                session.run("bump-my-version", "bump", "major", "--dry-run", "-vv")
            else:
                session.run("bump-my-version", "bump", "major")
        case "minor":
            log.info("Bumping minor version")
            
            if dry_run:
                session.log("Dry run enabled, no version bump will occur")
                session.run("bump-my-version", "bump", "minor", "--dry-run", "-vv")
            else:
                session.run("bump-my-version", "bump", "minor")
        case "patch":
            log.info("Bumping patch version")
            
            if dry_run:
                session.log("Dry run enabled, no version bump will occur")
                session.run("bump-my-version", "bump", "patch", "--dry-run", "-vv")
            else:
                session.run("bump-my-version", "bump", "patch")
        case _:
            raise ValueError(f"Invalid bump type: '{bump_type}'. Must be one of: {VALID_BUMP_TYPES}")

    

@nox.session(name="dev-env", tags=["setup"])
def dev(session: nox.Session) -> None:
    """Sets up a python development environment for the project.

    Run this on a fresh clone of the repository to automate building the project with uv.
    """
    install_uv_project(session, external=True)

@contextmanager
def cd(new_dir) -> t.Generator[None, t.Any, None]: # type: ignore
    """Context manager to change a directory before executing command."""
    prev_dir: str = os.getcwd()
    os.chdir(os.path.expanduser(new_dir))
    try:
        yield
    finally:
        os.chdir(prev_dir)
        

@nox.session(python=[DEFAULT_PYTHON], name="ruff-lint", tags=["ruff", "clean", "lint"])
def run_linter(session: nox.Session, lint_paths: list[str] = LINT_PATHS):
    """Nox session to run Ruff code linting."""
    if not Path("ruff.toml").exists():
        if not Path("pyproject.toml").exists():
            log.warning(
                """No ruff.toml file found. Make sure your pyproject.toml has a [tool.ruff] section!

If your pyproject.toml does not have a [tool.ruff] section, ruff's defaults will be used.
Double check imports in _init_.py files, ruff removes unused imports by default.
"""
            )

    session.install("ruff")

    log.info("Linting code")
    for d in lint_paths:
        if not Path(d).exists():
            log.warning(f"Skipping lint path '{d}', could not find path")
            pass
        else:
            lint_path: Path = Path(d)
            log.info(f"Running ruff imports sort on '{d}'")
            session.run(
                "ruff",
                "check",
                lint_path,
                "--select",
                "I",
                "--fix",
            )

            log.info(f"Running ruff checks on '{d}' with --fix")
            session.run(
                "ruff",
                "check",
                lint_path,
                "--fix",
            )

    log.info("Linting noxfile.py")
    session.run(
        "ruff",
        "check",
        f"{Path('./noxfile.py')}",
        "--fix",
    )
    
@nox.session(python=[DEFAULT_PYTHON], name="vulture-check", tags=["quality"])
def run_vulture_check(session: nox.Session):
    session.install(f"vulture")

    log.info("Checking for dead code with vulture")
    session.run("vulture", "src/pingpy", "--min-confidence", "100")
    

@nox.session(python=[DEFAULT_PYTHON], name="uv-export")
@nox.parametrize("requirements_output_dir", REQUIREMENTS_OUTPUT_DIR)
def export_requirements(session: nox.Session, requirements_output_dir: Path):
    ## Ensure REQUIREMENTS_OUTPUT_DIR path exists
    if not requirements_output_dir.exists():
        try:
            requirements_output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            msg = Exception(
                f"Unable to create requirements export directory: '{requirements_output_dir}'. Details: {exc}"
            )
            log.error(msg)

            requirements_output_dir: Path = Path("./")

    session.install(f"uv")

    log.info("Exporting production requirements")
    session.run(
        "uv",
        "pip",
        "compile",
        "pyproject.toml",
        "-o",
        str(REQUIREMENTS_OUTPUT_DIR / "requirements.txt"),
    )

## Run pytest with xdist, allowing concurrent tests
@nox.session(python=DEFAULT_PYTHON, name="tests")
def run_tests(session: nox.Session):
    install_uv_project(session)
    session.install("pytest-xdist")

    print("Running Pytest tests")
    session.run(
        "uv",
        "run",
        "pytest",
        "-n",
        "auto",
        "--tb=auto",
        "-v",
        "-rsXxfP",
    )

@nox.session(name="bump-version-init", tags=["release", "bump"])
def bump_version_init(session: nox.Session):
    session.install("bump-my-version")
    
    if not Path(".bumpversion.toml").exists():
        log.info("Initializing bump-my-version")
        session.run("bump-my-version", "sample-config", "--no-prompt", "--destination", ".bumpversion.toml")

@nox.session(name="bump-version-show", tags=["release", "bump"])
def bump_version_show_bumps(session: nox.Session):    
    session.install("bump-my-version")
    session.run("bump-my-version", "show-bump")

@nox.session(name="bump-version-patch", tags=["release", "bump"])
def bump_version_patch(session: nox.Session):
    
    bump_project_version(session=session, bump_type="patch")
    
@nox.session(name="bump-version-patch-dry", tags=["release", "bump"])
def bump_version_patch_dry(session: nox.Session):
    bump_project_version(session=session, bump_type="patch", dry_run=True)

@nox.session(name="bump-version-minor", tags=["release", "bump"])
def bump_version_minor(session: nox.Session):
    
    bump_project_version(session=session, bump_type="minor")
    
@nox.session(name="bump-version-minor-dry", tags=["release", "bump"])
def bump_version_minor_dry(session: nox.Session):
    bump_project_version(session=session, bump_type="minor", dry_run=True)

@nox.session(name="bump-version-major", tags=["release", "bump"])
def bump_version_patch(session: nox.Session):
    
    bump_project_version(session=session, bump_type="major")
    
@nox.session(name="bump-version-major-dry", tags=["release", "bump"])
def bump_version_patch_dry(session: nox.Session):
    bump_project_version(session=session, bump_type="major", dry_run=True)
