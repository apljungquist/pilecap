# pylint: disable=import-outside-toplevel
# ... because the import function must work without any dependencies installed in order
# to enable bootstrapping.
from __future__ import annotations

import argparse
import contextlib
import datetime
import json
import os
import pathlib
import subprocess
import tempfile
from typing import Dict, Iterator, List, Optional

from . import _env, _misc

CONSTRAINTS_LOCATION = "constraints"


def _flag_from_environ(name: str) -> bool:
    lut = {
        "1": True,
        "0": False,
        None: False,
    }
    return lut[os.environ.get(f"PILECAP_{name}")]


@contextlib.contextmanager
def _tmpdir() -> Iterator[pathlib.Path]:
    if _flag_from_environ("DEBUG"):
        yield pathlib.Path(
            tempfile.mkdtemp(
                prefix=datetime.datetime.now().strftime("tmp_%Y%m%d_%H%M%S"),
                dir=pathlib.Path.cwd(),
            )
        )
        return
    with tempfile.TemporaryDirectory() as wdir:
        yield pathlib.Path(wdir)


def _project_dir() -> pathlib.Path:
    """Return project root if it can be guessed"""
    result = pathlib.Path.cwd()
    pyproject_toml = result / "pyproject.toml"
    assert pyproject_toml.exists()
    return result


def _private_constraints_file(project_dir: pathlib.Path) -> pathlib.Path:
    return project_dir / "constraints" / f"{_env.fingerprint()}.txt"


def _header(markers: Dict[str, str], output_file: Optional[pathlib.Path]) -> List[str]:
    update_command = ["pilecap", "compile"]
    if output_file is not None:
        update_command += ["--output-file", str(output_file)]

    result = [
        "#",
        "# This file is autogenerated by pilecap in an environment like:",
        "#",
    ]
    result += [
        f"#  {line}"
        for line in json.dumps(
            markers, indent=2, separators=(",", ": "), sort_keys=True
        ).splitlines()
    ]
    result += [
        "#",
        "# To update, in an equivalent environment run:",
        "#",
        f"#   {' '.join(update_command)}",
        "#",
    ]
    return result


# Consider choosing requirements file from the header
# This would make it compatible with custom filenames thus making bootstrapping less
# awkward.
def _install(args: argparse.Namespace) -> None:
    constraints_file = _private_constraints_file(_project_dir())
    extra_env = {"PIP_CONSTRAINT": str(constraints_file)}
    if args.args:
        extra_args = args.args
    else:
        extra_args = ["-r", str(constraints_file)]
    subprocess.check_call(
        ["pip", "install"] + extra_args,
        env=_misc.dict_union(os.environ, extra_env),
    )


# Consider allowing arguments to be passed to pip-compile.
# In particular enabling --generate-hashes would be interesting.
def _compile(args: argparse.Namespace) -> None:
    from . import _compilation, _gathering

    project_root = _project_dir()
    markers = _env.markers()
    lines = _header(markers, args.output_file)

    if args.output_file is None:
        dst = _private_constraints_file(project_root)
    else:
        dst = args.output_file

    try:
        private_constraints = dst.open().readlines()
    except FileNotFoundError:
        private_constraints = []

    try:
        shared_constraints = _gathering.shared_constraints(project_root)
    except FileNotFoundError:
        shared_constraints = []
    with _tmpdir() as wdir:
        after = _compilation.updated_private_constraints(
            wdir=wdir,
            private_constraints=private_constraints,
            shared_constraints=shared_constraints,
            requirements=_gathering.requirements(project_root),
        )
        lines.append(after)
    dst.write_text("\n".join(lines + [""]))


def _build_requirements(args: argparse.Namespace) -> None:
    from . import _gathering

    for dep in sorted(_gathering.build_requirements(args.project_root)):
        print(dep)


def _run_requirements(args: argparse.Namespace) -> None:
    from . import _gathering

    for dep in sorted(_gathering.run_requirements(args.project_root)):
        print(dep)


def _parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    submain = result.add_subparsers(required=True)

    install_ = submain.add_parser(
        "install",
        help=(
            "Install package(s) using pip."
            " Passes any arguments to pip."
            " If none are given, all pinned packages will be installed."
        ),
    )
    install_.add_argument("args", nargs="*")
    install_.set_defaults(func=_install)

    compile_ = submain.add_parser(
        "compile",
        help="Compile constraints file",
    )
    compile_.add_argument(
        "--output-file",
        default=None,
        help="Update this constraints file instead of the default.",
        metavar="PATH",
        type=pathlib.Path,
    )
    compile_.set_defaults(func=_compile)

    plumbing = submain.add_parser(
        "plumbing",
        help="Access to low level functions",
    )
    subplumbing = plumbing.add_subparsers()
    breqs = subplumbing.add_parser(
        "build-requirements",
        help="Print all immediate dependencies for building the package",
    )
    breqs.add_argument("project_root", type=pathlib.Path)
    breqs.set_defaults(func=_build_requirements)
    rreqs = subplumbing.add_parser(
        "run-requirements",
        help="Print all immediate dependencies for running the package",
    )
    rreqs.add_argument("project_root", type=pathlib.Path)
    rreqs.set_defaults(func=_run_requirements)

    return result


def cli(args: List[str]) -> None:
    parsed = _parser().parse_args(args)
    parsed.func(parsed)