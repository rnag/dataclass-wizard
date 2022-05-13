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
