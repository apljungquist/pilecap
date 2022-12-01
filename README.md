# Pile Cap

_A stable foundation for reproducible builds_

More precisely this package aims to help install packages in a reproducible manner when
* only a single environment is targeted (one python version, one operating system, etc),
* multiple first party packages will be installed at the same time.

While the above may be a niche use case this package also provides some more general functions.
These can be used with a [layered pip-compile workflow](https://github.com/jazzband/pip-tools#workflow-for-layered-requirements) to facilitate locking all dependencies.

`pilecap plumbing build-requirements`
: Print direct dependencies for building package.

`pilecap plumbing run-requirements`
: Print direct dependencies for running package.
  Largely obsoleted by the `--all-extras` flag in `pip-compile`.