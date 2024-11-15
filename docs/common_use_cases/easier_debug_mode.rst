Easier Debug Mode
=================

While one way to see ``DEBUG`` level (or above) logs for this
library is to enable the ``debug_enabled`` flag in ``JSONWizard.Meta``,
this can sometimes be time-consuming, and still requires correct setup
of the ``logging`` module::

    import logging
    from dataclasses import dataclass

    from dataclass_wizard import JSONWizard


    logging.basicConfig(level='DEBUG')


    @dataclass
    class MyClass(JSONWizard):

        class _(JSONWizard.Meta):
            debug_enabled = True

An easier approach, is to pass in ``debug=True`` as shown below:


.. code:: python3

    from dataclasses import dataclass

    from dataclass_wizard import JSONWizard


    @dataclass
    class MyClass(JSONWizard, debug=True):

        class _(JSONWizard.Meta):
            skip_defaults = True
            key_transform_with_dump = 'PASCAL'

        my_bool: bool
        my_int: int = 2

        @classmethod
        def _pre_from_dict(cls, o):
            o['myBool'] = True
            return o


    # because of `debug=True` you should now see DEBUG
    # (and above) logs from this library, such as below.
    #
    # DEBUG:dataclass_wizard:Generated function code:
    #  def cls_fromdict(o):
    # DEBUG:dataclass_wizard:Generated function code:
    #  def cls_asdict(o:T,dict_factory=dict,...):

    c = MyClass.from_dict({'myBool': 'false'})
    print(c)
    # {
    #   "MyBool": true
    # }
