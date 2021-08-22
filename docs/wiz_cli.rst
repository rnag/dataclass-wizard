.. highlight:: shell

The CLI Tool
============

The ``wiz`` command provides a companion CLI tool for the Dataclass Wizard,
which further simplifies interaction with the Python ``dataclasses`` module.

Getting help::

    $ wiz -h
    usage: wiz [-h] [-v] [-q] {gen-schema,gs} ...

    A companion CLI tool for the Dataclass Wizard, which simplifies interaction with the Python
    `dataclasses` module.

    positional arguments:
      {gen-schema,gs}  Supported sub-commands
        gen-schema (gs)
                       Generates a Python dataclass schema, given a JSON input.

    optional arguments:
      -h, --help       show this help message and exit
      -v, --verbose    Enable verbose output
      -q, --quiet


To get help on a subcommand, simply use ``wiz <subcommand> -h``. For example::

    $ wiz gs -h

JSON To Dataclass
~~~~~~~~~~~~~~~~~

The subcommand ``gen-schema`` (aliased to ``gs``) provides a JSON to Python
schema generation tool. This utility takes a JSON file or string as an input,
and generates the corresponding dataclass schema. The main purpose is to easily
create dataclasses that can be used with API output, without resorting to
``dict``'s or ``NamedTuple``'s.

This scheme generation tool is inspired by the following projects:

-  https://github.com/mischareitsma/json2dataclass
-  https://russbiggs.github.io/json2dataclass
-  https://github.com/mholt/json-to-go
-  https://github.com/bermi/Python-Inflector


Example usage::

    echo '{
        "name": "Yavin IV",
        "rotation_period": "24",
        "orbital_period": "4818",
        "diameter": "10200",
        "climate": "temperate, tropical",
        "gravity": "1 standard",
        "terrain": "jungle, rainforests",
        "surface_water": "8",
        "population": "1000",
        "residents": [],
        "films": [
            "https://swapi.co/api/films/1/"
        ],
        "created": "2014-12-10T11:37:19.144000Z",
        "edited": "2014-12-20T20:58:18.421000Z",
        "url": "https://swapi.co/api/planets/3/"
    }' | wiz gs

Generates the following Python code::

    from dataclasses import dataclass
    from datetime import datetime
    from typing import Dict, List, Union


    @dataclass
    class Data:
        """
        Data dataclass

        """
        name: str
        rotation_period: Union[int, str]
        orbital_period: Union[int, str]
        diameter: Union[int, str]
        climate: str
        gravity: str
        terrain: str
        surface_water: Union[int, str]
        population: Union[int, str]
        residents: Dict
        films: List[str]
        created: datetime
        edited: datetime
        url: str


Note: to write the output to a Python file instead of displaying the
output in the terminal, pass the name of the output file. If the file
has no extension, a default ``.py`` extension will be added.

For example::

    # Note: the following command writes to a new file 'out.py'

    echo '<json string>' | wiz gs - out
