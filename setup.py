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
    'pytest~=6.2.4',
    'pytest-mock~=3.6.1',
    'pytest-cov~=2.12.1',
    'pytest-runner~=5.3.1'
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
        'Documentation': 'https://dataclass-wizard.readthedocs.io',
        'Source': 'https://github.com/rnag/dataclass-wizard',
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
        'Programming Language :: Python'
    ],
    test_suite='tests',
    tests_require=test_requirements,
    extras_require={
        'timedelta': ['pytimeparse>=1.1.7']
    },
    zip_safe=False
)
