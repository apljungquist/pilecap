import os
import pathlib
import re
import subprocess
from typing import Dict, Mapping, Sequence, Tuple

from pilecap._misc import Scope


def _write_pip_compile(
    dst: pathlib.Path,
    requirements: Sequence[pathlib.Path],
    hard_constraints: Sequence[pathlib.Path],
    soft_constraints: Sequence[pathlib.Path],
    strip_extras: bool = False,
) -> None:
    src = dst.with_suffix(dst.suffix + ".tmp")

    with src.open("x") as f:
        for r in requirements:
            f.write(f"-r {r}\n")
        for c in hard_constraints:
            f.write(f"-c {c}\n")

    with dst.open("x") as f:
        for c in soft_constraints:
            f.write(c.read_text())

    cmd = [
        "pip-compile",
        "--allow-unsafe",
        "--no-header",
        "--quiet",
        "--output-file",
        os.fspath(dst),
    ]
    if strip_extras:
        cmd.append("--strip-extras")
    cmd.append(os.fspath(src))
    subprocess.check_call(cmd)


def _intersection(keys_from: str, versions_from: str) -> Dict[str, str]:
    prog = re.compile(r"^\s*(?P<name>\S+)==(?P<version>\S+)\s*$", flags=re.MULTILINE)
    names = set(match.group("name") for match in prog.finditer(keys_from))
    versions = {
        match.group("name"): match.group("version")
        for match in prog.finditer(versions_from)
    }
    return {k: v for k, v in versions.items() if k in names}


def _write_intersection(
    dst: pathlib.Path, keys_from: pathlib.Path, versions_from: pathlib.Path
) -> None:
    with dst.open("x") as f:
        items = _intersection(keys_from.read_text(), versions_from.read_text()).items()
        for name, version in sorted(items):
            f.write(f"{name}=={version}\n")


def _pretty(wdir: pathlib.Path, text: str) -> str:
    return re.sub(
        f"-(?P<flag>[cr]) {wdir}/(?P<name>.+)\\.[cr]\\.txt",
        "-\\g<flag> \\g<name>",
        text,
        flags=re.MULTILINE,
    )


# The following mostly-acyclic directed dag describes the compilation hierarchy:
#
# shared requirements 0 -+--------------------------------------------------------+
# shared requirements n -+--------------------------------------------------------+
# shared constraints ----+-----------------------+                                |
#                        +- shared requirements -+                                |
#                                                +- effective shared constraints -+
# private requirements 0 ---------------------------------------------------------+
# private requirements m ---------------------------------------------------------+
# private constraints  -----------------------------------------------------------+-
def updated_private_constraints(
    wdir: pathlib.Path,
    private_constraints: Sequence[str],
    shared_constraints: Sequence[str],
    requirements: Mapping[str, Tuple[Scope, Sequence[str]]],
) -> str:
    # pylint: disable=too-many-locals
    # ... because the locals are mostly constants referring to file names, and it feels
    # like trying to decompose this function further would only make it harder to read.

    # Name reuse would raise thanks to x flag but declaring these together still helps
    # provide an overview.
    # Consider finding an API in pip-compile that does not require the file system
    private_constraints_in = wdir / "private_constraints_in.txt"
    private_constraints_out = wdir / "private_constraints_out.txt"
    shared_constraints_in = wdir / "shared_constraints.txt"
    shared_requirements = wdir / "shared_requirements.txt"
    # Named just shared to make the output look nice
    effective_shared_constraints = wdir / "shared.c.txt"

    def req_file(name: str) -> pathlib.Path:
        # None of the files above end with .r.txt ensuring absence of collisions
        return wdir / f"{name}.r.txt"

    with private_constraints_in.open("x") as f:
        for constraint in private_constraints:
            f.write(constraint)
            f.write("\n")

    with shared_constraints_in.open("x") as f:
        for constraint in shared_constraints:
            f.write(constraint)
            f.write("\n")

    for name, (_, lines) in requirements.items():
        # None of the files created by this function ends with
        with req_file(name).open("x") as f:
            for line in lines:
                f.write(line)
                f.write("\n")

    _write_pip_compile(
        dst=shared_requirements,
        requirements=[
            req_file(name)
            for name, (scope, _) in requirements.items()
            if scope is Scope.SHARED
        ],
        hard_constraints=[shared_constraints_in],
        # The soft constraints here should not affect the final result, but
        # I think they may improve speed.
        soft_constraints=[private_constraints_in],
        strip_extras=False,
    )

    # Prevent unconstrained packages from misleadingly being annotated with
    # "via -c shared".
    _write_intersection(
        effective_shared_constraints,
        keys_from=shared_constraints_in,
        versions_from=shared_requirements,
    )

    _write_pip_compile(
        dst=private_constraints_out,
        requirements=[req_file(name) for name in requirements],
        hard_constraints=[effective_shared_constraints],
        soft_constraints=[private_constraints_in],
        strip_extras=True,
    )

    return _pretty(wdir, private_constraints_out.read_text())
