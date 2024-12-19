"""The setup script."""
import itertools
import pathlib

from pkg_resources import parse_requirements
from setuptools import setup, find_packages


here = pathlib.Path(__file__).parent

package_name = 'dataclass_wizard'

packages = find_packages(include=[package_name, f'{package_name}.*'])

requires = [
    'typing-extensions>=4.9.0; python_version <= "3.12"'
]

if (requires_dev_file := here / 'requirements-dev.txt').exists():
    with requires_dev_file.open() as requires_dev_txt:
        dev_requires = [str(req) for req in parse_requirements(requires_dev_txt)]
else:   # Running on CI
    dev_requires = []

if (requires_docs_file := here / 'docs' / 'requirements.txt').exists():
    with requires_docs_file.open() as requires_docs_txt:
        doc_requires = [str(req) for req in parse_requirements(requires_docs_txt)]
else:   # Running on CI
    doc_requires = []

if (requires_test_file := here / 'requirements-test.txt').exists():
    with requires_test_file.open() as requires_test_txt:
        test_requirements = [str(req) for req in parse_requirements(requires_test_txt)]
else:   # Running on CI
    test_requirements = []

if (requires_bench_file := here / 'requirements-bench.txt').exists():
    with requires_bench_file.open() as requires_bench_txt:
        bench_requirements = [str(req) for req in parse_requirements(requires_bench_txt)]
else:   # Running on CI
    bench_requirements = []

# extras_require = {
#     'dotenv': ['python-dotenv>=0.19.0'],
# }

# Ref: https://stackoverflow.com/a/71166228/10237506
# extras_require['all'] = list(itertools.chain.from_iterable(extras_require.values()))

about = {}
exec((here / package_name / '__version__.py').read_text(), about)

readme = (here / 'README.rst').read_text(encoding='utf-8')
history = (here / 'HISTORY.rst').read_text(encoding='utf-8')

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
    package_data={
        # Include all .pyi files in your package directories
        '': ['*.pyi'],
    },
    include_package_data=True,
    install_requires=requires,
    project_urls={
        'Discussions': 'https://github.com/rnag/dataclass-wizard/discussions',
        'Changelog': 'https://dataclass-wizard.readthedocs.io/en/latest/history.html',
        'Source': 'https://github.com/rnag/dataclass-wizard',
        'Download': 'https://pypi.org/project/dataclass-wizard',
        'Documentation': 'https://dataclass-wizard.readthedocs.io',
        'Bug Tracker': 'https://github.com/rnag/dataclass-wizard/issues',
    },
    license=about['__license__'],
    keywords=[
        'dataclasses', 'wizard', 'json', 'serialization', 'deserialization',
        'dataclass serialization', 'type hints', 'performance', 'alias',
        'python', 'env', 'dotenv', 'lightweight'
    ],
    classifiers=[
        # Ref: https://pypi.org/classifiers/
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3',
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
        'dotenv': ['python-dotenv>=1,<2'],
        'timedelta': ['pytimeparse>=1.1.7'],
        'toml': [
            'tomli>=2,<3; python_version=="3.9"',
            'tomli>=2,<3; python_version=="3.10"',
            'tomli-w>=1,<2'
        ],
        'yaml': ['PyYAML>=6,<7'],
        'dev': dev_requires + doc_requires + test_requirements + bench_requirements,
    },
    zip_safe=False
)
