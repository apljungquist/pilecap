import contextlib
import dataclasses
import os
import pathlib
import shutil
import subprocess
import sys
import textwrap
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

import pytest

from pilecap import _cli, _compilation, _env

_RESOURCES = pathlib.Path(__file__).with_suffix("")
_REPO = pathlib.Path(__file__).parents[1]
_CONSTRAINTS = "constraints.txt"


@contextlib.contextmanager
def _environ(**kwargs: Optional[str]) -> None:
    old = {k: os.environ.get(k) for k in kwargs if k in os.environ}
    for k, v in kwargs.items():
        if v is None:
            del os.environ[k]
        else:
            os.environ[k] = v
    try:
        yield
    finally:
        for k, v in old.items():
            if v is None:
                del os.environ[k]
            else:
                os.environ[k] = v


@dataclasses.dataclass(frozen=True)
class _PackageIndex:
    location: pathlib.Path

    @property
    def links(self) -> pathlib.Path:
        return self.location / "links"

    def _download(self, cmd: List[str]) -> None:
        # TODO: Consider making _PackageIndex a contect manager instead
        with _environ(PIP_NO_INDEX=None):
            subprocess.check_call(
                ["pip", "download", "--no-deps", f"--dest={self.links}"] + cmd
            )

    def download_explicit(self, packages: Iterable[Tuple[str, str]]) -> None:
        """Download packages with specified version into index"""
        self._download([f"{name}=={version}" for name, version in packages])

    def download_implicit(self, packages: List[str]) -> None:
        """Download packages with some, reproducible version into index"""
        # pylint: disable=protected-access
        # ... because I cannot be bothered fixing this right now.
        with _environ(PIP_CONSTRAINT=str(_cli._private_constraints_file(_REPO))):
            self._download(packages)


# TODO: Improve isolation
# Somehow test_make_workflow required me to install some packages such as fire but not
# canaria-domestica-red on my machine in order to pass. Then, in CI, it predictably
# failed because the latter had not been downloaded.
@pytest.fixture()
def _package_index(tmp_path) -> Iterator[_PackageIndex]:
    package_index = _PackageIndex(tmp_path / "package_index")
    with _environ(
        PIP_FIND_LINKS=str(package_index.links),
        PIP_NO_INDEX="1",
    ):
        yield package_index


# The package does not matter as long as it
# 1. is not normally installed, and
# 2. is the same in the uninstall and install functions.
def _uninstall_canary() -> None:
    subprocess.check_call(["pip", "uninstall", "--yes", "canaria-domestica-red"])


def _install_canary() -> None:
    subprocess.check_call(["pip", "install", "canaria-domestica-red"])


# Sanity check for the package index isolation
def test_pip_install_fails_with_empty_index(_package_index):
    _uninstall_canary()
    with pytest.raises(Exception):
        _install_canary()


# Sanity check for the package index isolation
def test_pip_install_succeeds_with_populated_index(
    _package_index: _PackageIndex,
) -> None:
    _package_index.download_implicit(["canaria-domestica-red"])
    _uninstall_canary()
    _install_canary()


def _package_versions(text: str) -> Dict[str, str]:
    result = {}
    for line in text.splitlines():
        prefix = line.split("#")[0].strip()
        if not prefix:
            continue  # Ignore lines that are all comment
        if prefix.startswith("--"):
            continue  # Ignore flags such as --find-links
        k, v = prefix.split("==")
        result[k] = v
    return result


def only_on_reference():
    # Some tests expect hard coded output that depends on the platform.
    # With this marker a test will run only on the reference platform.
    return pytest.mark.skipif(
        (sys.version_info.major, sys.version_info.minor) != (3, 10)
        or sys.platform != "linux",
        reason="Compilation result can be different on different platforms",
    )


# Note that this is buggy:
# if a package is not in shared constraints, but
# the package is in the runtime requirements then
# pip-compile is free to pick any version thus
# ignoring whatever is in the old constraints file.
# TODO: Update to match the automatic workflow
@only_on_reference()
def test_make_workflow(_package_index: _PackageIndex, tmp_path):
    """Tests the make workflow that is assisted by this tool"""
    wdir = tmp_path / "project"

    def check_call(cmd):
        subprocess.check_call(cmd, cwd=wdir)

    # Test scenario where canaria-domestica-red has been added to install_requires
    # and is pinned globally (if it was not the compilation would fail, at least
    # with the current resolver).
    expected = _package_versions((_RESOURCES / _CONSTRAINTS).read_text())
    shutil.copytree(_RESOURCES / "project", wdir)

    # TODO: Consider downloading multiple versions of each package
    # While only one version is available for each package pip-compile cannot choose
    # the wrong version. This is not critical since the main purpose of this test is
    # to exercise the interfaces of this package and, to a lesser extent, the
    # interfaces between this package and pip-tools. Still, multiple versions would be
    # a relatively cheap way to expand coverage.
    _package_index.download_implicit(["wheel"])
    _package_index.download_explicit(expected.items())

    # Sanity check
    before = _package_versions((wdir / _CONSTRAINTS).read_text())
    assert before != expected

    # This may not work on systems with low time resolution since we could end up
    # touching pyproject.toml in the same instance as we copied all the files.
    check_call(["touch", "constraints.txt"])
    check_call(["touch", "pyproject.toml"])
    check_call(["make", _CONSTRAINTS])

    after = _package_versions((wdir / _CONSTRAINTS).read_text())
    assert after == expected


def test_pretty():
    # pylint:disable=protected-access
    before = textwrap.dedent(
        """\
        pip==22.1.1
            # via
            #   -c /tmp/20220529_121935_42k_fbk6/shared.c.txt
            #   -r /tmp/20220529_121935_42k_fbk6/run.r.txt
            #   pip-tools
        setuptools==62.3.2
            # via
            #   -r /tmp/20220529_121935_42k_fbk6/dev.foo.r.txt
            #   astroid
            #   pip-tools
            #   setuptools-scm
        """
    )
    expected = textwrap.dedent(
        """\
        pip==22.1.1
            # via
            #   -c shared
            #   -r run
            #   pip-tools
        setuptools==62.3.2
            # via
            #   -r dev.foo
            #   astroid
            #   pip-tools
            #   setuptools-scm
        """
    )
    actual = _compilation._pretty(
        pathlib.Path("/tmp/20220529_121935_42k_fbk6/"), before
    )
    assert actual == expected


def test_intersection():
    # pylint:disable=protected-access
    keys_from = textwrap.dedent(
        """\
        setuptools==62.3.2
            # via setuptools-scm
        """
    )
    versions_from = textwrap.dedent(
        """\
        pip==22.1.1
            # via
            #   -c shared
            #   -r run
            #   pip-tools
        setuptools==62.3.2
            # via
            #   -r dev
            #   astroid
            #   pip-tools
            #   setuptools-scm
        """
    )
    actual = _compilation._intersection(keys_from, versions_from)
    expected = {"setuptools": "62.3.2"}
    assert actual == expected


def test_environment_fingerprint_is_available():
    assert _env.fingerprint()


def test_header_does_not_raise():
    # pylint: disable=protected-access
    # ... because I cannot be bothered fixing this right now.
    _cli._header(_env.markers(), None)
