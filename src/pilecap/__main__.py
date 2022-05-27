import pathlib
from typing import Union

import fire

import pilecap


def build_requirements(package: Union[pathlib.Path, str]) -> None:
    """Print all immediate dependencies for building `package`"""
    package = pathlib.Path(package)
    assert package.name == "pyproject.toml"
    for dep in sorted(pilecap.build_dependencies(package.parent)):
        print(dep)


def run_requirements(package: Union[pathlib.Path, str]) -> None:
    """Print all immediate dependencies for running `package`"""
    package = pathlib.Path(package)
    assert package.name == "pyproject.toml"
    for dep in sorted(pilecap.run_requirements(package.parent)):
        print(dep)


def main() -> None:
    fire.Fire(
        {
            "build_requirements": build_requirements,
            "run_requirements": run_requirements,
        }
    )
