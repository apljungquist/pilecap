import pathlib
import shutil
import subprocess
import sys
import textwrap

import pytest

from pilecap import compilation

_RESOURCES = pathlib.Path(__file__).with_suffix("")

_CONSTRAINTS = "constraints.txt"


def only_on_reference():
    # Some tests expect hard coded output that depends on the platform.
    # With this marker a test will run only on the reference platform.
    return pytest.mark.skipif(
        (sys.version_info.major, sys.version_info.minor) != (3, 10)
        or sys.platform != "linux",
        reason="Compilation result can be different on different platforms",
    )


# Considering that the main goal of this project is reproducible tests
# it is ironic that this test depends on pypi.
# TODO: Isolate tests like this from pypi
# Note that this is buggy:
# if a package is not in shared constraints, but
# the package is in the runtime requirements then
# pip-compile is free to pick any version thus
# ignoring whatever is in the old constraints file.
# TODO: Update to match the automatic workflow
@only_on_reference()
def test_make_workflow(tmp_path):
    """Tests the make workflow that is assisted by this tool"""
    wdir = tmp_path / "project"

    def check_call(cmd):
        subprocess.check_call(cmd, cwd=wdir)

    # Test scenario where canaria-domestica-red has been added to install_requires
    # and is pinned globally (if it was not the compilation would fail, at least
    # with the current resolver).
    expected = (_RESOURCES / _CONSTRAINTS).read_text()
    shutil.copytree(_RESOURCES / "project", wdir)

    # Sanity check
    before = (wdir / _CONSTRAINTS).read_text()
    assert before != expected

    # This may not work on systems with low time resolution since we could end up
    # touching pyproject.toml in the same instance as we copied all the files.
    check_call(["touch", "constraints.txt"])
    check_call(["touch", "pyproject.toml"])
    check_call(["make", _CONSTRAINTS])

    after = (wdir / _CONSTRAINTS).read_text()
    assert after == expected


def test_pretty():
    # pylint:disable=protected-access
    before = textwrap.dedent(
        """\
        pip==22.1.1
            # via
            #   -c /tmp/20220529_121935_42k_fbk6/shared.txt
            #   -r /tmp/20220529_121935_42k_fbk6/run.in
            #   pip-tools
        setuptools==62.3.2
            # via
            #   -r /tmp/20220529_121935_42k_fbk6/dev.in
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
            #   -r dev
            #   astroid
            #   pip-tools
            #   setuptools-scm
        """
    )
    actual = compilation._pretty(pathlib.Path("/tmp/20220529_121935_42k_fbk6/"), before)
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
    actual = compilation._intersection(keys_from, versions_from)
    expected = {"setuptools": "62.3.2"}
    assert actual == expected
