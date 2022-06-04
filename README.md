# Pile Cap

_A stable foundation for reproducible builds_


## Value proposition
This project aims to be both a map and a vehicle to reproducible builds.
It adopts the progressive disclosure pattern to accommodate both novices and veterans.
For the novice _porcelain_ commands can be used to set up a simple workflow.
For the veteran _plumbing_ commands can be combined with other tools such as `pip` and `pip-tools` to create more complicated workflows.

It also throws in support for sharing constraints between projects to make it easier installing them into the same environment.


## Alternatives
The functionality of this package is mostly implemented by many other packages but none implements all of it
* `pip` has virtually no support for locking python versions.
* `pip-tools`
  * cannot read `build-system.requires`,
  * has no option to include all extras, and 
  * leaves it to the user to correctly use constraints files correctly with pip.
* `pipenv` makes no attempt at supporting multiple, concurrent environments.
* `poetry` does not allow advanced use cases such as sharing constraints between projects.
  (admittedly I have not looked closely).
* `bazel` / `pants` probably provide better reproducibility but require a significant departure from the workflows that are familiar from many open source projects. 


## Installation

The `install` command works without any dependencies making it possible to bootstrap `pilecap` like

```bash
pip install --no-deps 'pilecap==x.y'
pilecap install pilecap
```
