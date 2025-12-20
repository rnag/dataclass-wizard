from __future__ import annotations

import pytest

from dataclasses import dataclass
from ipaddress import IPv4Address

from dataclass_wizard import JSONWizard, LoadMeta
from dataclass_wizard.errors import ParseError
from dataclass_wizard import DumpMixin, LoadMixin


def test_register_type_ipv4address_roundtrip():

    @dataclass
    class Foo(JSONWizard):
        s: str | None = None
        c: IPv4Address | None = None

    Foo.register_type(IPv4Address)

    data = {"c": "127.0.0.1", "s": "foobar"}

    foo = Foo.from_dict(data)
    assert foo.c == IPv4Address("127.0.0.1")

    assert foo.to_dict() == data
    assert Foo.from_dict(foo.to_dict()).to_dict() == data


def test_ipv4address_without_hook_raises_parse_error():

    @dataclass
    class Foo(JSONWizard):
        c: IPv4Address | None = None

    data = {"c": "127.0.0.1"}

    with pytest.raises(ParseError) as e:
        Foo.from_dict(data)

    assert e.value.phase == 'load'

    msg = str(e.value)
    # assert "field `c`" in msg
    assert "not currently supported" in msg
    assert "IPv4Address" in msg
    assert "load" in msg.lower()


def test_ipv4address_hooks_with_load_and_dump_mixins_roundtrip():
    @dataclass
    class Foo(JSONWizard, DumpMixin, LoadMixin):
        c: IPv4Address | None = None

        @classmethod
        def load_to_ipv4_address(cls, o, *_):
            return IPv4Address(o)

        @classmethod
        def dump_from_ipv4_address(cls, o, *_):
            return str(o)

    Foo.register_load_hook(IPv4Address, Foo.load_to_ipv4_address)
    Foo.register_dump_hook(IPv4Address, Foo.dump_from_ipv4_address)

    data = {"c": "127.0.0.1"}

    foo = Foo.from_dict(data)
    assert foo.c == IPv4Address("127.0.0.1")

    assert foo.to_dict() == data
    assert Foo.from_dict(foo.to_dict()).to_dict() == data
