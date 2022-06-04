from __future__ import annotations

import sys

from pilecap import _cli


def main() -> None:
    _cli.cli(sys.argv[1:])
