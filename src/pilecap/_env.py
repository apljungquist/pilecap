import enum
import hashlib
import json
import os
import platform
import sys
from typing import Dict

from pilecap._typing import assert_never


def _implementation_version() -> str:
    if hasattr(sys, "implementation"):
        version = sys.implementation.version
        return f"{version.major}.{version.minor}.{version.micro}"
    return "0"


class _Marker(enum.Enum):
    """Environment markers and their value in the current environment

    This list is adapted from PEP 508 and should be exhaustive
    (https://peps.python.org/pep-0508/#environment-markers).
    """

    OS_NAME = "os_name"
    SYS_PLATFORM = "sys_platform"
    PLATFORM_MACHINE = "platform_machine"
    PLATFORM_PYTHON_IMPLEMENTATION = "platform_python_implementation"
    PLATFORM_RELEASE = "platform_release"
    PLATFORM_SYSTEM = "platform_system"
    PLATFORM_VERSION = "platform_version"
    PYTHON_VERSION = "python_version"
    PYTHON_FULL_VERSION = "python_full_version"
    IMPLEMENTATION_NAME = "implementation_name"
    IMPLEMENTATION_VERSION = "implementation_version"

    @property
    def current_value(self) -> str:
        # pylint: disable=too-many-return-statements
        # ... because I cannot immediately think of a better way
        if self is _Marker.OS_NAME:
            return os.name
        if self is _Marker.SYS_PLATFORM:
            return sys.platform
        if self is _Marker.PLATFORM_MACHINE:
            return platform.machine()
        if self is _Marker.PLATFORM_PYTHON_IMPLEMENTATION:
            return platform.python_implementation()
        if self is _Marker.PLATFORM_RELEASE:
            return platform.release()
        if self is _Marker.PLATFORM_SYSTEM:
            return platform.system()
        if self is _Marker.PLATFORM_VERSION:
            return platform.version()
        if self is _Marker.PYTHON_VERSION:
            return ".".join(platform.python_version_tuple()[:2])
        if self is _Marker.PYTHON_FULL_VERSION:
            return platform.python_version()
        if self is _Marker.IMPLEMENTATION_NAME:
            return sys.implementation.name
        if self is _Marker.IMPLEMENTATION_VERSION:
            return _implementation_version()
        assert_never(self)


# Including all possible markers would make the fingerprint too unstable, even the
# build date of the host system is available.
def fingerprint() -> str:
    """Return a fingerprint for the current environment

    Note that this is does not capture only some common markers and there are others
    that could affect the compilation of constraints.
    """
    parts = [
        # Include some markers in the filename to make it easier to inspect.
        _Marker.PYTHON_VERSION.current_value,
        # Include a checksum based on all markers to ensure files are unique.
        hashlib.md5(json.dumps(markers(), sort_keys=True).encode()).hexdigest()[:8],
    ]
    return "-".join(parts)


# Consider inspecting popular packages to see what markers are actually used
# Consider making configurable in pyproject.toml
def markers() -> Dict[str, str]:
    """Return markers used by fingerprint and their values"""
    return {
        variant.name.lower(): variant.current_value
        for variant in [
            _Marker.PYTHON_VERSION,
            # While I do not use this it is a common marker and helps illustrate that
            # while all markers are reflected in the fingerprint not all are included
            # in their plain form.
            _Marker.OS_NAME,
        ]
    }
