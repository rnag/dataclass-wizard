"""Opt-in exact Literal loading and metadata isolation regressions."""

from dataclasses import dataclass
from enum import IntEnum
from typing import Literal, TypedDict, Union

import pytest

from dataclass_wizard import EnvMeta, EnvWizard, JSONWizard, LoadMeta, fromdict
from dataclass_wizard.env import env_config
from dataclass_wizard.errors import ParseError


class Number(IntEnum):
    """Integer enum values that compare equal to ints and bools."""
    ZERO = 0
    ONE = 1


@pytest.mark.parametrize(
    'annotation,value,accepted',
    [
        (Literal[0], 0, True),
        (Literal[0], False, False),
        (Literal[0], 0.0, False),
        (Literal[0], Number.ZERO, False),
        (Literal[False], False, True),
        (Literal[False], 0, False),
        (Literal[1], 1, True),
        (Literal[1], True, False),
        (Literal[1], 1.0, False),
        (Literal[True], True, True),
        (Literal[True], 1, False),
        (Literal[Number.ONE], Number.ONE, True),
        (Literal[Number.ONE], 1, False),
        (Literal[Number.ONE], True, False),
        (Literal['ready'], 'ready', True),
        (Literal['ready'], 'other', False),
        (Literal[None], None, True),
    ],
)
def test_strict_literal_type_and_value(annotation, value, accepted):
    """Require an exact type and value after opting in."""
    @dataclass
    class Model(JSONWizard):
        """Local model whose metadata is isolated to this test."""
        class _(JSONWizard.Meta):
            strict_mode_for_literals = True

        item: annotation

    if accepted:
        result = Model.from_dict({'item': value})
        assert result.item is value
    else:
        with pytest.raises(ParseError) as caught:
            Model.from_dict({'item': value})
        assert caught.value.field_name == 'item'


@pytest.mark.parametrize('value', [0, False, Number.ZERO])
def test_strict_literal_keeps_equal_values_of_distinct_types(value):
    """Keep equal-valued alternatives with different types distinct."""
    @dataclass
    class Model(JSONWizard):
        """Local model whose metadata is isolated to this test."""
        class _(JSONWizard.Meta):
            strict_mode_for_literals = True

        item: Literal[0, False, Number.ZERO]

    assert Model.from_dict({'item': value}).item is value
    with pytest.raises(ParseError):
        Model.from_dict({'item': 0.0})


@pytest.mark.parametrize('explicit_false', [False, True])
def test_literal_default_remains_permissive(explicit_false):
    """Preserve the default and explicitly disabled value-only mode."""
    @dataclass
    class Model(JSONWizard):
        """Local model whose metadata is isolated to this test."""
        item: Literal[0]

    if explicit_false:
        LoadMeta(strict_mode_for_literals=False).bind_to(Model)

    assert Model.from_dict({'item': False}).item is False


def test_loadmeta_can_enable_strict_literals():
    """Allow explicit LoadMeta binding on a plain dataclass."""
    @dataclass
    class Model:
        """Local model whose metadata is isolated to this test."""
        item: Literal[0]

    LoadMeta(strict_mode_for_literals=True).bind_to(Model)
    assert fromdict(Model, {'item': 0}).item == 0
    with pytest.raises(ParseError):
        fromdict(Model, {'item': False})


def test_strict_literal_inside_containers():
    """Apply the selected mode inside nested collection elements."""
    @dataclass
    class Model(JSONWizard):
        """Local model whose metadata is isolated to this test."""
        class _(JSONWizard.Meta):
            strict_mode_for_literals = True

        items: list[dict[str, Literal[0]]]

    assert Model.from_dict({'items': [{'x': 0}]}).items == [{'x': 0}]
    with pytest.raises(ParseError):
        Model.from_dict({'items': [{'x': False}]})


@pytest.mark.parametrize('strict_first', [False, True])
def test_nested_literal_helpers_preserve_each_class_mode(strict_first):
    """Keep sibling class metadata independent in either field order."""
    @dataclass
    class Strict(JSONWizard):
        """Nested model with exact Literal matching enabled."""
        class _(JSONWizard.Meta):
            strict_mode_for_literals = True

        item: Literal[0]

    @dataclass
    class Loose(JSONWizard):
        """Nested model preserving value-only Literal matching."""
        class _(JSONWizard.Meta):
            strict_mode_for_literals = False

        item: Literal[0]

    first_type, second_type = (
        (Strict, Loose) if strict_first else (Loose, Strict)
    )

    @dataclass
    class Model(JSONWizard):
        """Local model whose metadata is isolated to this test."""
        first: first_type
        second: second_type

    good = {'first': {'item': 0}, 'second': {'item': 0}}
    good['second' if strict_first else 'first']['item'] = False
    result = Model.from_dict(good)
    loose = result.second if strict_first else result.first
    assert loose.item is False

    bad = {'first': {'item': 0}, 'second': {'item': 0}}
    bad['first' if strict_first else 'second']['item'] = False
    with pytest.raises(ParseError):
        Model.from_dict(bad)


@pytest.mark.parametrize('recursive', [False, True])
def test_strict_literal_meta_cascades_only_when_recursive(recursive):
    """Apply own metadata and only cascade it when configured."""
    @dataclass
    class Child:
        """Shared child model containing a Literal field."""
        item: Literal[0]

    @dataclass
    class Model(JSONWizard):
        """Local model whose metadata is isolated to this test."""
        class _(JSONWizard.Meta):
            strict_mode_for_literals = True

        child: Child
        own: Literal[0]

    LoadMeta(recursive=recursive).bind_to(Model)
    assert Model.from_dict({'child': {'item': 0}, 'own': 0}).own == 0
    with pytest.raises(ParseError):
        Model.from_dict({'child': {'item': 0}, 'own': False})
    if recursive:
        with pytest.raises(ParseError):
            Model.from_dict({'child': {'item': False}, 'own': 0})
    else:
        result = Model.from_dict({'child': {'item': False}, 'own': 0})
        assert result.child.item is False


@pytest.mark.parametrize('strict_first', [False, True])
def test_shared_child_keeps_each_root_mode(strict_first):
    """Keep reused child types independent across root loaders."""
    @dataclass
    class Child:
        """Shared child model containing a Literal field."""
        item: Literal[0]

    @dataclass
    class Strict(JSONWizard):
        """Nested model with exact Literal matching enabled."""
        class _(JSONWizard.Meta):
            strict_mode_for_literals = True

        child: Child

    @dataclass
    class Loose(JSONWizard):
        """Nested model preserving value-only Literal matching."""
        child: Child

    roots = (Strict, Loose) if strict_first else (Loose, Strict)
    for root in roots:
        assert root.from_dict({'child': {'item': 0}}).child.item == 0
        if root is Strict:
            with pytest.raises(ParseError):
                root.from_dict({'child': {'item': False}})
        else:
            result = root.from_dict({'child': {'item': False}})
            assert result.child.item is False


def test_literal_mode_inherited_from_meta_base():
    """Honor explicitly inherited Meta configuration."""
    class Parent(JSONWizard):
        """A base model carrying inherited strict configuration."""
        class _(JSONWizard.Meta):
            strict_mode_for_literals = True

    @dataclass
    class Model(Parent):
        """Local model whose metadata is isolated to this test."""
        class _(Parent._):
            pass

        item: Literal[0]

    assert Model.from_dict({'item': 0}).item == 0
    with pytest.raises(ParseError):
        Model.from_dict({'item': False})


def test_strict_literal_optional_and_union_values():
    """Preserve optional and union alternatives with strict matching."""
    @dataclass
    class Model(JSONWizard):
        """Local model whose metadata is isolated to this test."""
        class _(JSONWizard.Meta):
            strict_mode_for_literals = True

        item: Union[Literal[0], Literal[1], None]

    for value in (0, 1, None):
        assert Model.from_dict({'item': value}).item is value
    for value in (False, True, 0.0, 1.0):
        with pytest.raises(ParseError):
            Model.from_dict({'item': value})


@pytest.mark.parametrize('strict', [None, False, True])
def test_env_literal_typed_values_and_default_mode(strict):
    """Validate typed Env values without changing the default mode."""
    class Model(EnvWizard):
        """Local model whose metadata is isolated to this test."""
        item: Literal[0]

    if strict is not None:
        EnvMeta(strict_mode_for_literals=strict).bind_to(Model)

    assert Model(__env__=env_config(mapping={}), item=0).item == 0
    if strict:
        with pytest.raises(ParseError):
            Model(__env__=env_config(mapping={}), item=False)
    else:
        assert Model(__env__=env_config(mapping={}), item=False).item is False


def test_env_literal_main_meta_applies_without_recursive_config():
    """Apply Env root metadata even when recursion is disabled."""
    class Model(EnvWizard):
        """Local model whose metadata is isolated to this test."""
        class _(EnvWizard.Meta):
            strict_mode_for_literals = True
            recursive = False

        item: Literal[0]

    assert Model(__env__=env_config(mapping={}), item=0).item == 0
    with pytest.raises(ParseError):
        Model(__env__=env_config(mapping={}), item=False)


@pytest.mark.parametrize('strict', [False, True])
def test_env_literal_string_values_remain_strings(strict):
    """Load only declared string alternatives from synthetic Env data."""
    class Model(EnvWizard):
        """Local model whose metadata is isolated to this test."""
        item: Literal['ready']

    EnvMeta(strict_mode_for_literals=strict).bind_to(Model)
    assert Model(__env__=env_config(mapping={'ITEM': 'ready'})).item == 'ready'
    with pytest.raises(ParseError):
        Model(__env__=env_config(mapping={'ITEM': 'other'}))


@pytest.mark.parametrize('strict', [False, True])
def test_env_literal_raw_integer_string_is_not_coerced(strict):
    """Do not introduce integer coercion for raw environment strings."""
    class Model(EnvWizard):
        """Local model whose metadata is isolated to this test."""
        item: Literal[0]

    EnvMeta(strict_mode_for_literals=strict).bind_to(Model)
    with pytest.raises(ParseError):
        Model(__env__=env_config(mapping={'ITEM': '0'}))


@pytest.mark.parametrize('strict_first', [False, True])
def test_optional_typed_dict_keeps_each_class_literal_mode(strict_first):
    """Keep cached optional TypedDict loaders scoped to each class."""
    class Payload(TypedDict, total=False):
        """An optional literal field reused across loading modes."""
        code: Literal[0]

    @dataclass
    class Strict(JSONWizard):
        """Nested model with exact Literal matching enabled."""
        class _(JSONWizard.Meta):
            strict_mode_for_literals = True

        value: Payload

    @dataclass
    class Loose(JSONWizard):
        """Nested model preserving value-only Literal matching."""
        value: Payload

    first_type, second_type = ((Strict, Loose) if strict_first
                               else (Loose, Strict))

    @dataclass
    class Outer(JSONWizard):
        """A root model loading both sibling metadata modes."""
        first: first_type
        second: second_type

    strict_field, loose_field = (('first', 'second') if strict_first
                                 else ('second', 'first'))
    valid = {'first': {'value': {}}, 'second': {'value': {}}}
    valid[strict_field]['value']['code'] = 0
    valid[loose_field]['value']['code'] = False
    result = Outer.from_dict(valid)
    assert getattr(result, strict_field).value['code'] == 0
    assert getattr(result, loose_field).value['code'] is False
    valid[strict_field]['value']['code'] = False
    with pytest.raises(ParseError):
        Outer.from_dict(valid)
