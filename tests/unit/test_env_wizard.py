from __future__ import annotations

import os
from typing import ClassVar

from dataclass_wizard import EnvWizard


def test_load():
    os.environ.update({
        'hello_world': 'Test',
        'MyStr': 'This STRING',
        'MY_TEST_VALUE123': '11',
        'THIS_Num': '23',
        'my_list': '["1", 2, "3", "4.5", 5.7]',
        'my_other_list': 'rob@test.org, this@email.com , hello-world_123@tst.org,z@ab.c'
    })

    class MyClass(EnvWizard):
        # these are class-level fields, and should be ignored
        my_cls_var: ClassVar[str]
        other_var = 21

        my_str: str
        this_num: int
        my_list: list[int]
        my_other_list: list[str]
        my_test_value123: int = 21
        # missing from environment
        my_field_not_in_env: str = 'testing'

    assert not hasattr(MyClass, 'my_cls_var')
    assert MyClass.other_var == 21

    assert MyClass.my_str == 'This STRING'
    assert MyClass.this_num == 23
    assert MyClass.my_list == [1, 2, 3, 4, 6]
    assert MyClass.my_other_list == ['rob@test.org', 'this@email.com', 'hello-world_123@tst.org', 'z@ab.c']
    assert MyClass.my_test_value123 == 11
    assert MyClass.my_field_not_in_env == 'testing'


def test_load_with_dict():
    os.environ.update({
        'MY_DICT': '{"123": "True", "5": "false"}',
        'My.Other.Dict': 'some_key=value,  anotherKey=123 ,LastKey=just a test~'
    })

    class ClassWithDict(EnvWizard, reload_env=True):

        class _(EnvWizard.Meta):
            field_to_env_var = {'my_other_dict': 'My.Other.Dict'}

        # these are class-level fields, and should be ignored
        my_dict: dict[int, bool]
        my_other_dict: dict[str, int | str]

    assert ClassWithDict.my_dict == {123: True, 5: False}

    # note that the value for 'anotherKey' is a string value ('123') here,
    # but we might want to see if we can update it to a numeric value (123)
    # instead.
    assert ClassWithDict.my_other_dict == {
        'some_key': 'value',
        'anotherKey': '123',
        'LastKey': 'just a test~',
    }
