"""The setup script."""
import pathlib

from setuptools import setup, find_packages


here = pathlib.Path(__file__).parent

package_name = 'dataclass_wizard'

packages = find_packages(include=[package_name, f'{package_name}.*'])

requires = [
    'typing-extensions>=3.7.4.2; python_version <= "3.9"',
    'dataclasses; python_version == "3.6"',
    'backports-datetime-fromisoformat==1.0.0; python_version == "3.6"'
]

test_requirements = [
    'pytest==6.2.4',
    'pytest-mock==3.6.1',
    'pytest-cov==2.12.1',
    'pytest-runner==5.3.1'
]

about = {}
exec((here / package_name / '__version__.py').read_text(), about)

readme = (here / 'README.rst').read_text()
history = (here / 'HISTORY.rst').read_text()

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__description__'],
    long_description=readme,
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    packages=packages,
    entry_points={
        'console_scripts': [
            'wiz=wizard_cli.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requires,
    project_urls={
        'Documentation': 'https://dataclass-wizard.readthedocs.io',
        'Source': 'https://github.com/rnag/dataclass-wizard',
    },
    license=about['__license__'],
    keywords=['dataclasses', 'dataclass', 'wizard', 'json', 'marshal',
              'property', 'field-property', 'serialization', 'deserialization',
              'json2dataclass'],
    classifiers=[
        # Ref: https://pypi.org/classifiers/
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    zip_safe=False
)
