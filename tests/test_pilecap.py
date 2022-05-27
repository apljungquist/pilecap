import pathlib
import shutil
import subprocess

_RESOURCES = pathlib.Path(__file__).with_suffix("")

_CONSTRAINTS = "constraints.txt"


def test_make_workflow(tmp_path):
    """Tests the make workflow that is assisted by this tool"""

    def check_call(cmd):
        subprocess.check_call(cmd, cwd=tmp_path)

    # Test scenario where canaria-domestica-red has been added to install_requires
    # and is pinned globally (if it was not the compilation would fail, at least
    # with the current resolver).
    expected = (_RESOURCES / _CONSTRAINTS).read_text()
    shutil.copytree(_RESOURCES / "project", tmp_path, dirs_exist_ok=True)

    # Sanity check
    before = (tmp_path / _CONSTRAINTS).read_text()
    assert before != expected

    # This may not work on systems with low time resolution since we could end up
    # touching pyproject.toml in the same instance as we copied all the files.
    check_call(["touch", "constraints.txt"])
    check_call(["touch", "pyproject.toml"])
    check_call(["make", _CONSTRAINTS])

    after = (tmp_path / _CONSTRAINTS).read_text()
    assert after == expected
