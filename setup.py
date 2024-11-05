"""The setup script."""
import pathlib

from pkg_resources import parse_requirements
from setuptools import setup, find_packages


here = pathlib.Path(__file__).parent

package_name = 'dataclass_wizard'

packages = find_packages(include=[package_name, f'{package_name}.*'])

requires = [
    'typing-extensions>=3.7.4.2; python_version <= "3.9"',
    'dataclasses; python_version == "3.6"',
    'backports-datetime-fromisoformat==1.0.0; python_version == "3.6"'
]

# TODO update once we drop support for Python 3.6 & 3.7
# if (requires_dev_file := here / 'requirements-dev.txt').exists():
requires_dev_file = here / 'requirements-dev.txt'
if requires_dev_file.exists():
    with requires_dev_file.open() as requires_dev_txt:
        dev_requires = [str(req) for req in parse_requirements(requires_dev_txt)]
else:   # Running on CI
    dev_requires = []

# TODO update once we drop support for Python 3.6 & 3.7
# if (requires_docs_file := here / 'docs' / 'requirements.txt').exists():
requires_docs_file = here / 'docs' / 'requirements.txt'
if requires_docs_file.exists():
    with requires_docs_file.open() as requires_docs_txt:
        doc_requires = [str(req) for req in parse_requirements(requires_docs_txt)]
else:   # Running on CI
    doc_requires = []

# TODO update once we drop support for Python 3.6 & 3.7
# if (requires_test_file := here / 'requirements-test.txt').exists():
requires_test_file = here / 'requirements-test.txt'
if requires_test_file.exists():
    with requires_test_file.open() as requires_test_txt:
        test_requirements = [str(req) for req in parse_requirements(requires_test_txt)]
else:   # Running on CI
    test_requirements = []

about = {}
exec((here / package_name / '__version__.py').read_text(), about)

readme = (here / 'README.rst').read_text()
history = (here / 'HISTORY.rst').read_text()

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__description__'],
    long_description=readme,
    long_description_content_type='text/x-rst',
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    packages=packages,
    entry_points={
        'console_scripts': [
            f'wiz={package_name}.wizard_cli.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requires,
    project_urls={
        'Changelog': 'https://dataclass-wizard.readthedocs.io/en/latest/history.html',
        'Source': 'https://github.com/rnag/dataclass-wizard',
        'Download': 'https://pypi.org/project/dataclass-wizard',
        'Documentation': 'https://dataclass-wizard.readthedocs.io',
        'Bug Tracker': 'https://github.com/rnag/dataclass-wizard/issues',
    },
    license=about['__license__'],
    keywords=['dataclasses', 'dataclass', 'wizard', 'json', 'marshal',
              'json to dataclass', 'json2dataclass', 'dict to dataclass',
              'property', 'field-property',
              'serialization', 'deserialization'],
    classifiers=[
        # Ref: https://pypi.org/classifiers/
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python'
    ],
    test_suite='tests',
    tests_require=test_requirements,
    extras_require={
        'timedelta': ['pytimeparse>=1.1.7'],
        'yaml': ['PyYAML>=5.3'],
        'dev': dev_requires + doc_requires + test_requirements,
    },
    zip_safe=False
)
