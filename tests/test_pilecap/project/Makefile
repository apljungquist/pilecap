.DELETE_ON_ERROR: ;

SHELL=/bin/bash

build/requirements/build.txt: pyproject.toml
	mkdir -p $(@D)
	pilecap plumbing build-requirements $(<D) > $@

build/requirements/global.in: constraints/global.txt build/requirements/run.txt
	mkdir -p $(@D)
	if [ -f $@ ]; then rm $@; fi
	echo "-c ../../constraints/global.txt" >> $@
	echo "-r run.txt" >> $@

build/requirements/global.txt: build/requirements/global.in
	mkdir -p $(@D)
	pip-compile --allow-unsafe --quiet --output-file $@ $<

build/requirements/run.txt: pyproject.toml
	mkdir -p $(@D)
	pilecap plumbing run-requirements $(<D) > $@

constraints.txt: build/requirements/build.txt build/requirements/global.txt $(wildcard requirements/*.txt)
	pip-compile --allow-unsafe --strip-extras --quiet --output-file $@ $^
