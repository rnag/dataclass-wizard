Wizard Mixin Classes
====================

In addition to the :class:`JSONWizard`, here a few extra Wizard Mixin
classes that might prove to be quite convenient to use.


:class:`EnvWizard`
~~~~~~~~~~~~~~~~~~

Effortlessly load environment variables and ``.env`` files into typed schemas. Supports secrets via files (file names as keys).

Automatically applies the ``@dataclass`` decorator and supports type hinting with
string-to-type conversion. Requires subclass instantiation to function.

For a detailed example and advanced features:

- 📖 `Full Documentation <https://dcw.ritviknag.com/en/latest/env_magic.html>`_

:class:`JSONPyWizard`
~~~~~~~~~~~~~~~~~~~~~

A subclass of :class:`JSONWizard` that disables the default key transformation behavior,
ensuring that keys are not transformed during JSON serialization (e.g., no ``camelCase`` transformation).

.. code-block:: python3

    class JSONPyWizard(JSONWizard):
        """Helper for JSONWizard that ensures dumping to JSON keeps keys as-is."""

        def __init_subclass__(cls, str=True, debug=False):
            """Bind child class to DumpMeta with no key transformation."""
            DumpMeta(key_transform='NONE').bind_to(cls)
            super().__init_subclass__(str, debug)


Use Case
--------

Use :class:`JSONPyWizard` when you want to prevent the automatic ``camelCase`` conversion of dictionary keys during serialization, keeping them in their original ``snake_case`` format.

:class:`JSONListWizard`
~~~~~~~~~~~~~~~~~~~~~~~

The JSON List Wizard is a Mixin class that extends :class:`JSONWizard` to
return :class:`Container` - instead of ``list`` - objects.

.. note:: :class:`Container` objects are simply convenience wrappers around
  a collection of dataclass instances. For all intents and purposes, they
  behave exactly the same as ``list`` objects, with some added helper methods:

    * :meth:`prettify` - Convert the list of instances to a *prettified* JSON
      string.

    * :meth:`to_json` - Convert the list of instances to a JSON string.

    * :meth:`to_json_file` - Serialize the list of instances and write it to a
      JSON file.

Simple example of usage below:

.. code:: python3

    from __future__ import annotations  # Note: In 3.10+, this import can be removed

    from dataclasses import dataclass

    from dataclass_wizard import JSONListWizard, Container


    @dataclass
    class Outer(JSONListWizard):
        my_str: str | None
        inner: list[Inner]


    @dataclass
    class Inner:
        other_str: str


    my_list = [
        {"my_str": 20,
         "inner": [{"otherStr": "testing 123"}]},
        {"my_str": "hello",
         "inner": [{"otherStr": "world"}]},
    ]

    # De-serialize the JSON string into a list of `MyClass` objects
    c = Outer.from_list(my_list)

    # Container is just a sub-class of list
    assert isinstance(c, list)
    assert type(c) == Container

    print(c)
    # [Outer(my_str='20', inner=[Inner(other_str='testing 123')]),
    #  Outer(my_str='hello', inner=[Inner(other_str='world')])]

    print(c.prettify())
    # [
    #   {
    #     "myStr": "20",
    #   ...

    # serializes the list of dataclass instances to a JSON file
    c.to_json_file('my_file.json')

:class:`JSONFileWizard`
~~~~~~~~~~~~~~~~~~~~~~~

The JSON File Wizard is a *minimalist* Mixin class that makes it easier
to interact with JSON files, as shown below.

It comes with only two added methods: :meth:`from_json_file` and
:meth:`to_json_file`.

.. note::
  This can be paired with the :class:`JSONWizard` Mixin class for more
  complete extensibility.

.. code:: python3

    from __future__ import annotations  # Note: In 3.10+, this import can be removed

    from dataclasses import dataclass

    from dataclass_wizard import JSONFileWizard


    @dataclass
    class MyClass(JSONFileWizard):
        my_str: str | None
        my_int: int = 14


    c1 = MyClass(my_str='Hello, world!')
    print(c1)

    # Serializes the dataclass instance to a JSON file
    c1.to_json_file('my_file.json')

    # contents of my_file.json:
    #> {"myStr": "Hello, world!", "myInt": 14}

    c2 = MyClass.from_json_file('my_file.json')

    # assert that data is the same
    assert c1 == c2

:class:`YAMLWizard`
~~~~~~~~~~~~~~~~~~~

The YAML Wizard leverages the `PyYAML`_ library -- which can be installed
as an extra via ``pip install dataclass-wizard[yaml]`` -- to easily convert
dataclass instances to/from YAML.

.. note::
  The default key transform used in the YAML dump process is `lisp-case`,
  however this can easily be customized without the need to sub-class
  from :class:`JSONWizard`, as shown below.

      >>> @dataclass
      >>> class MyClass(YAMLWizard, key_transform='CAMEL'):
      >>>     ...

A (mostly) complete example of using the :class:`YAMLWizard` is as follows:

.. code:: python3

    from __future__ import annotations  # Note: In 3.10+, this import can be removed

    from dataclasses import dataclass, field

    from dataclass_wizard import YAMLWizard


    @dataclass
    class MyClass(YAMLWizard):
        str_or_num: str | int = 42
        nested: MyNestedClass | None = None


    @dataclass
    class MyNestedClass:
        list_of_map: list[dict[int, str]] = field(default_factory=list)
        my_int: int = 14


    c1 = MyClass.from_yaml("""
    str-or-num: 23
    nested:
        ListOfMap:
            - 111: Hello,
              222: World!
            - 333: 'Testing'
              444: 123
    """)

    # serialize the dataclass instance to a YAML file
    c1.to_yaml_file('my_file.yaml')

    # sample contents of `my_file.yaml` would be:
    #> nested:
    #>   list-of-map:
    #>   - 111: Hello,
    #>   ...

    # now read it back...
    c2 = MyClass.from_yaml_file('my_file.yaml')

    # assert we get back the same data
    assert c1 == c2

    # let's create a list of dataclass instances
    objects = [MyClass(), c2, MyClass(3, nested=MyNestedClass())]

    # and now, serialize them all...
    yaml_string = MyClass.list_to_yaml(objects)

    print(yaml_string)
    # - nested: null
    #   str-or-num: 42
    # - nested:
    #     list-of-map:
    #   ...

.. _PyYAML: https://pypi.org/project/PyYAML/

:class:`TOMLWizard`
~~~~~~~~~~~~~~~~~~~

.. admonition:: **Added in v0.28.0**

   The :class:`TOMLWizard` was introduced in version 0.28.0.

The TOML Wizard provides an easy, convenient interface for converting ``dataclass`` instances to/from `TOML`_. This mixin enables simple loading, saving, and flexible serialization of TOML data, including support for custom key casing transforms.

.. note::
   By default, *NO* key transform is used in the TOML dump process. This means that a `snake_case` field name in Python is saved as `snake_case` in TOML. However, this can be customized without subclassing from :class:`JSONWizard`, as below.

       >>> @dataclass
       >>> class MyClass(TOMLWizard, key_transform='CAMEL'):
       >>>     ...

Dependencies
------------
- For reading TOML, `TOMLWizard` uses `Tomli`_ for Python 3.9 and 3.10, and the built-in `tomllib`_ for Python 3.11+.
- For writing TOML, `Tomli-W`_ is used across all Python versions.

.. _TOML: https://toml.io/en/
.. _Tomli: https://pypi.org/project/tomli/
.. _Tomli-W: https://pypi.org/project/tomli-w/
.. _tomllib: https://docs.python.org/3/library/tomllib.html

Example
-------

A (mostly) complete example of using the :class:`TOMLWizard` is as follows:

.. code:: python3

    from dataclasses import dataclass, field
    from dataclass_wizard import TOMLWizard


    @dataclass
    class InnerData:
        my_float: float
        my_list: list[str] = field(default_factory=list)


    @dataclass
    class MyData(TOMLWizard):
        my_str: str
        my_dict: dict[str, int] = field(default_factory=dict)
        inner_data: InnerData = field(default_factory=lambda: InnerData(3.14, ["hello", "world"]))


    # TOML input string with nested tables and lists
    toml_string = """
    my_str = 'example'
    [my_dict]
    key1 = 1
    key2 = '2'

    [inner_data]
    my_float = 2.718
    my_list = ['apple', 'banana', 'cherry']
    """

    # Load from TOML string
    data = MyData.from_toml(toml_string)

    # Sample output of `data` after loading from TOML:
    #> my_str = 'example'
    #> my_dict = {'key1': 1, 'key2': 2}
    #> inner_data = InnerData(my_float=2.718, my_list=['apple', 'banana', 'cherry'])

    # Save to TOML file
    data.to_toml_file('data.toml')

    # Now read it back from the TOML file
    new_data = MyData.from_toml_file('data.toml')

    # Assert we get back the same data
    assert data == new_data, "Data read from TOML file does not match the original."

    # Create a list of dataclass instances
    data_list = [data, new_data, MyData("another_example", {"key3": 3}, InnerData(1.618, ["one", "two"]))]

    # Serialize the list to a TOML string
    toml_output = MyData.list_to_toml(data_list, header='testing')

    print(toml_output)
    # [[testing]]
    # my_str = "example"
    #
    # [testing.my_dict]
    # key1 = 1
    # key2 = 2
    #
    # [testing.inner_data]
    # my_float = 2.718
    # my_list = [
    #     "apple",
    #     "banana",
    #     "cherry",
    # ]
    # ...

This approach provides a straightforward way to handle TOML data within Python dataclasses.

Methods
-------

.. method:: from_toml(cls, string_or_stream, *, decoder=None, header='items', parse_float=float)

   Parses a TOML `string` or stream and converts it into an instance (or list of instances) of the dataclass. If `header` is provided and the corresponding value in the parsed data is a list, the return type is `List[T]`.

   **Example usage:**

      >>> data_str = '''my_str = "test"\n[inner]\nmy_float = 1.2'''
      >>> obj = MyClass.from_toml(data_str)

.. method:: from_toml_file(cls, file, *, decoder=None, header='items', parse_float=float)

   Reads the contents of a TOML file and converts them into an instance (or list of instances) of the dataclass. Similar to :meth:`from_toml`, it can return a list if `header` is specified and points to a list in the TOML data.

   **Example usage:**

      >>> obj = MyClass.from_toml_file('config.toml')

.. method:: to_toml(self, /, *encoder_args, encoder=None, multiline_strings=False, indent=4)

   Converts a dataclass instance to a TOML string. Optional parameters include `multiline_strings` for enabling/disabling multiline formatting of strings and `indent` for setting the indentation level.

   **Example usage:**

      >>> toml_str = obj.to_toml()

.. method:: to_toml_file(self, file, mode='wb', encoder=None, multiline_strings=False, indent=4)

   Serializes a dataclass instance and writes it to a TOML file. By default, opens the file in "write binary" mode.

   **Example usage:**

      >>> obj.to_toml_file('output.toml')

.. method:: list_to_toml(cls, instances, header='items', encoder=None, **encoder_kwargs)

   Serializes a list of dataclass instances into a TOML string, grouped under a specified `header`.

   **Example usage:**

      >>> obj_list = [MyClass(), MyClass(my_str="example")]
      >>> toml_str = MyClass.list_to_toml(obj_list)
