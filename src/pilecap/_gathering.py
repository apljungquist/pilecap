import itertools
import os
import pathlib
import re
from typing import Dict, Iterable, List, Tuple

import build
import pep517
from build import util

from pilecap._misc import Scope

ALL_DISTRIBUTIONS = ("editable", "sdist", "wheel")


def _remove_extras_marker(requirement: str) -> str:
    """Return requirement without any extras markers
    >>> _remove_extras_marker("fire (>=0.4) ; extra == 'cli'")
    'fire (>=0.4)'
    """
    return re.sub(r"\s*;\s*extra\s*==\s*'[^']+'", "", requirement)


def run_requirements(project_dir: pathlib.Path) -> List[str]:
    return [
        _remove_extras_marker(requirement)
        for requirement in util.project_wheel_metadata(project_dir).get_all(
            "Requires-Dist"
        )
        or []
    ]


def build_requirements(
    project_dir: pathlib.Path, distributions: Iterable[str]
) -> List[str]:
    builder = build.ProjectBuilder(
        os.fspath(project_dir),
        runner=pep517.quiet_subprocess_runner,
    )
    return sorted(
        set(
            itertools.chain(
                builder.build_system_requires,
                *[builder.get_requires_for_build(dist) for dist in distributions],
            )
        )
    )


def _other_requirements(file: pathlib.Path) -> List[str]:
    return file.read_text().splitlines()


def requirements(project_dir: pathlib.Path) -> Dict[str, Tuple[Scope, List[str]]]:
    result = {
        "build": (Scope.PRIVATE, build_requirements(project_dir, ALL_DISTRIBUTIONS)),
        "run": (Scope.SHARED, run_requirements(project_dir)),
    }
    for file in project_dir.glob("requirements/*.txt"):
        key = file.stem
        if key in result:
            raise RuntimeError(
                f"Expected requirements name other than build or run, but got {key}"
            )
        result[key] = (Scope.PRIVATE, _other_requirements(file))
    return result


def shared_constraints(project_dir: pathlib.Path) -> List[str]:
    file = project_dir / "constraints" / "shared.txt"
    return file.open().readlines()
