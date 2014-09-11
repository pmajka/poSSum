.PHONY: clean-pyc clean-build docs clean

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "test - run tests quickly with the default Python"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package and upload a release"
	@echo "dist - package"

clean: clean-build clean-pyc
	rm -fr htmlcov/
	rm -rf docs/build

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

test:
	python setup.py test

coverage-gather:
	coverage run --source possum.__init__ --source possum.deformable_histology_iterations,possum.pos_common,possum.pos_deformable_wrappers,possum.pos_parameters,possum.pos_wrapper_skel,possum.pos_wrappers,possum.pos_color,possum.pos_segmentation_parser setup.py test

coverage: coverage-gather
	coverage report -m
	coverage html
	firefox htmlcov/index.html

docs:
#	sphinx-apidoc -o docs/ possum
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	firefox docs/build/html/index.html

release: clean
	python setup.py sdist upload
	python setup.py bdist_wheel upload

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist
