import os
import pathlib
import re
from typing import Set

import build
import pep517
from build import util


def build_dependencies(src_dir: pathlib.Path) -> Set[str]:
    builder = build.ProjectBuilder(
        os.fspath(src_dir),
        runner=pep517.quiet_subprocess_runner,
    )
    return builder.build_system_requires


def _remove_extras_marker(requirement: str) -> str:
    """Return requirement without any extras markers
    >>> _remove_extras_marker("fire (>=0.4) ; extra == 'cli'")
    'fire (>=0.4)'
    """
    return re.sub(r"\s*;\s*extra\s*==\s*'[^']+'", "", requirement)


def run_requirements(path: pathlib.Path) -> Set[str]:
    return set(
        _remove_extras_marker(requirement)
        for requirement in util.project_wheel_metadata(path).get_all("Requires-Dist")
        or []
    )
