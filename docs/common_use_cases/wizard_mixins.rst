Wizard Mixin Classes
====================

In addition to the :class:`JSONWizard`, here a few extra Wizard Mixin
classes that might prove to be quite convenient to use.

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
