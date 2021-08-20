Map a JSON Key to a Field
=========================

The ``dataclass-wizard`` library provides a set of built-in *key transform* helper
functions that automatically transform the casing of keys in a JSON or Python
``dict`` object to and from dataclass field names. As mentioned in the
:doc:`Meta <meta>` section, this key transform only applies to dataclasses
at present, not to keys in ``dict`` objects or to sub-classes of
`NamedTuple`_ or `TypedDict`_, for example.

When converting a JSON key to a dataclass field name, the key transform function
defaults to :func:`to_snake_case`, which converts all JSON keys to -
*you guessed it!* - `snake case`_, which is the leading convention in Python. Therefore, a JSON key
appearing as *myField*, *MYField*, *MyField*, or *my-field* will all implicitly
be mapped to a dataclass field named ``my_field`` by default. When converting
the dataclass field back to JSON, the default key transform function is
:func:`to_camel_case`, which transforms it back to ``myField`` in this case.
It's also possible to update the key transform functions used, as explained in
the :doc:`Meta <meta>` section.

However, suppose you want to instead create a custom mapping of a JSON key to a
dataclass field name. For example, a key appears in the JSON object as
``myJSONKey`` (case-sensitive), and you want to map it to a dataclass
field that is declared as ``my_str``.

The below example demonstrates how to set up a custom mapping of a JSON key name
to a dataclass field. There a few different options available, so feel free to
choose whichever approach is most preferable. I am myself partial to the last
approach, as I find it to be the most explicit, and also one that plays well
with IDEs in general.

.. note:: The mapping of JSON key to field below is only in *addition* to the
  default key transform as mentioned above. For example, ``myNewField`` is already
  mapped to a ``my_new_field`` dataclass field, and the inverse is also true.

.. code:: python3

    from dataclasses import dataclass
    from typing_extensions import Annotated

    from dataclass_wizard import JSONSerializable, json_field, json_key


    @dataclass
    class MyClass(JSONSerializable):

        # 1-- Define a mapping for JSON key to dataclass field in the inner
        #     `Meta` subclass.
        class Meta(JSONSerializable.Meta):
            json_key_to_field = {
                'myJSONKey': 'my_str'
            }

        # 2-- Using a sub-class of `Field`. This can be considered as an
        #     alias to the helper function `dataclasses.field`.
        my_str: str = json_field(["myField", "myJSONKey"])

        # 3-- Using `Annotated` with a `json_key` (or :class:`JSON`) argument.
        my_str: Annotated[str, json_key('myField', 'myJSONKey')]

One thing to note is that the mapping to each JSON key name is case-sensitive,
so passing *myfield* (all lowercase) will not match a *myField* key in a
JSON or Python ``dict`` object.

In either case, you can confirm that the custom key mapping works as expected:

.. code:: python3

    def main():

        string = """
        {"myJSONKey": "hello world!"}
        """

        c = MyClass.from_json(string)
        print(repr(c))
        # prints:
        #   MyClass(my_str='hello world!')

        print(c)
        # prints:
        #   {
        #     "myStr": "hello world!"
        #   }


    if __name__ == '__main__':
        main()


Map a Field Back to a JSON Key
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, the reverse mapping (dataclass field to JSON key) will not
automatically be associated by default.

You can pass the ``all`` parameter (or an :attr:`__all__` key, in the case
of a dictionary) to also associate the inverse mapping, as shown below.

.. note:: If multiple JSON keys are specified for a dataclass field, only
  the first one provided will be used to map a field name to a JSON key.

Using the :class:`Meta` approach
--------------------------------

.. code:: python3

    from typing import Union
    from dataclasses import dataclass

    from dataclass_wizard import JSONSerializable


    @dataclass
    class MyClass(JSONSerializable):

        class Meta(JSONSerializable.Meta):

            json_key_to_field = {
                # Pass `__all__` so the inverse mapping is also added.
                '__all__': True,
                # If there are multiple JSON keys for a field, the one that is
                # first defined is used in the dataclass field to JSON key mapping.
                'myJSONKey': 'my_str',
                'myField': 'my_str',
                'someBoolValue': 'my_bool',
            }

        my_str: str
        my_bool: Union[bool, str]

Using a :func:`dataclasses.Field` subclass
------------------------------------------

.. code:: python3

    from typing import Union
    from dataclasses import dataclass

    from dataclass_wizard import JSONSerializable, json_field


    @dataclass
    class MyClass(JSONSerializable):
        my_str: str = json_field(
            ('myJSONKey',
             'myField'),
            # Pass `all` so the inverse mapping is also added.
            all=True
        )

        my_bool: Union[bool, str] = json_field(
            'someBoolValue', all=True
        )

Using Annotated with a :func:`json_key` argument
------------------------------------------------

.. code:: python3

    from dataclasses import dataclass
    from typing import Union
    from typing_extensions import Annotated

    from dataclass_wizard import JSONSerializable, json_key


    @dataclass
    class MyClass(JSONSerializable):

        my_str: Annotated[str,
                          # If there are multiple JSON keys listed for a
                          # dataclass field, the one that is defined first
                          # will be used.
                          json_key('myJSONKey', 'myField', all=True)]

        my_bool: Annotated[Union[bool, str],
                           json_key('someBoolValue', all=True)]


In all the above cases, the custom key mappings apply for both the *load*
and *dump* process, so now the below behavior is observed:

.. code:: python3

    def main():

        string = """
        {"myJSONKey": "hello world!", "someBoolValue": "TRUE"}
        """

        c = MyClass.from_json(string)
        print(repr(c))
        # prints:
        #   MyClass(my_str='hello world!', my_bool='TRUE')

        print(c)
        # prints:
        #   {
        #     "myJSONKey": "hello world!",
        #     "someBoolValue": "TRUE"
        #   }


    if __name__ == '__main__':
        main()


.. _NamedTuple: https://docs.python.org/3.8/library/typing.html#typing.NamedTuple
.. _TypedDict: https://docs.python.org/3.8/library/typing.html#typing.TypedDict
.. _snake case: https://en.wikipedia.org/wiki/Snake_case
