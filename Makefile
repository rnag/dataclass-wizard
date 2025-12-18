.PHONY: clean clean-test clean-pyc clean-build docs help
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

init: ## install all dev dependencies for this project
	pip install -e .[dev]

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -type f -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

lint: ## check style with flake8 and pylint
	flake8 dataclass_wizard tests
	pylint dataclass_wizard tests

test: ## run unit tests quickly with the default Python
	pytest -v --cov=dataclass_wizard --cov-report=term-missing tests/unit

test-vb: ## run unit tests (in verbose mode) with the default Python
	pytest -vvv --log-cli-level=DEBUG --capture=tee-sys --cov=dataclass_wizard --cov-report=term-missing tests/unit

test-all: ## run tests on every Python version with tox
	tox

coverage: ## check code coverage with unit tests quickly with the default Python
	coverage run --source dataclass_wizard -m pytest tests/unit
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/dataclass_wizard.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ dataclass_wizard
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(BROWSER) docs/_build/html/index.html

servedocs: docs ## compile the docs watching for changes
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

release: dist ## package and upload a release
	twine upload dist/*

check: dist-local  ## verify release before upload to PyPI
	twine check dist/*

dist: clean ## builds source and wheel package
	pip install build
	python -m build
	ls -l dist

dist-local: clean replace_version ## builds source and wheel package (for local testing)
	pip install build
	python -m build
	ls -l dist
	$(MAKE) revert_readme

replace_version: ## replace |version| in README.rst with the current version
	cp README.rst README.rst.bak
	python -c "import re; \
from pathlib import Path; \
version = re.search(r\"__version__\\s*=\\s*'(.+?)'\", Path('dataclass_wizard/__version__.py').read_text()).group(1); \
readme_path = Path('README.rst'); \
readme_content = readme_path.read_text(); \
readme_path.write_text(readme_content.replace('|version|', version)); \
print(f'Replaced version in {readme_path}: {version}')"

revert_readme: ## revert README.rst to its original state
	mv README.rst.bak README.rst

install: clean ## install the package to the active Python's site-packages
	pip install .

dist-conda: clean ## builds source and wheel package for Anaconda
	conda build .

release-conda: dist-conda ## package and upload a release to Anaconda
	$(eval DIST_FILE=$(shell conda build . --output))
	anaconda upload $(DIST_FILE)
