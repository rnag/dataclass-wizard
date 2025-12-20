from __future__ import annotations

import pytest

from dataclasses import dataclass
from ipaddress import IPv4Address

from dataclass_wizard import register_type, JSONWizard, LoadMeta, fromdict, asdict
from dataclass_wizard.errors import ParseError
from dataclass_wizard.v1 import DumpMixin, LoadMixin
from dataclass_wizard.v1.models import TypeInfo, Extras


def test_v1_register_type_ipv4address_roundtrip():

    @dataclass
    class Foo(JSONWizard):
        class Meta(JSONWizard.Meta):
            v1 = True

        b: bytes = b""
        s: str | None = None
        c: IPv4Address | None = None

    Foo.register_type(IPv4Address)

    data = {"b": "AAAA", "c": "127.0.0.1", "s": "foobar"}

    foo = Foo.from_dict(data)
    assert foo.c == IPv4Address("127.0.0.1")

    assert foo.to_dict() == data
    assert Foo.from_dict(foo.to_dict()).to_dict() == data


def test_v1_ipv4address_without_hook_raises_parse_error():

    @dataclass
    class Foo(JSONWizard):
        class Meta(JSONWizard.Meta):
            v1 = True

        c: IPv4Address | None = None

    data = {"c": "127.0.0.1"}

    with pytest.raises(ParseError) as e:
        Foo.from_dict(data)

    assert e.value.phase == 'load'

    msg = str(e.value)
    assert "field `c`" in msg
    assert "not currently supported" in msg
    assert "IPv4Address" in msg
    assert "load" in msg.lower()


def test_v1_meta_codegen_hooks_ipv4address_roundtrip():

    def load_to_ipv4_address(tp: TypeInfo, extras: Extras) -> str:
        return tp.wrap(tp.v(), extras)

    def dump_from_ipv4_address(tp: TypeInfo, extras: Extras) -> str:
        return f"str({tp.v()})"

    @dataclass
    class Foo(JSONWizard):
        class Meta(JSONWizard.Meta):
            v1 = True
            v1_type_to_load_hook = {IPv4Address: load_to_ipv4_address}
            v1_type_to_dump_hook = {IPv4Address: dump_from_ipv4_address}

        b: bytes = b""
        s: str | None = None
        c: IPv4Address | None = None

    data = {"b": "AAAA", "c": "127.0.0.1", "s": "foobar"}

    foo = Foo.from_dict(data)
    assert foo.c == IPv4Address("127.0.0.1")

    assert foo.to_dict() == data
    assert Foo.from_dict(foo.to_dict()).to_dict() == data


def test_v1_meta_runtime_hooks_ipv4address_roundtrip():

    @dataclass
    class Foo(JSONWizard):
        class Meta(JSONWizard.Meta):
            v1 = True
            v1_type_to_load_hook = {IPv4Address: ('runtime', IPv4Address)}
            v1_type_to_dump_hook = {IPv4Address: ('runtime', str)}

        b: bytes = b""
        s: str | None = None
        c: IPv4Address | None = None

    data = {"b": "AAAA", "c": "127.0.0.1", "s": "foobar"}

    foo = Foo.from_dict(data)
    assert foo.c == IPv4Address("127.0.0.1")

    assert foo.to_dict() == data
    assert Foo.from_dict(foo.to_dict()).to_dict() == data

    # invalid modes should raise an error
    with pytest.raises(ValueError) as e:
        meta = LoadMeta(v1_type_to_load_hook={IPv4Address: ('RT', str)})
        meta.bind_to(Foo)
        assert "mode must be 'runtime' or 'v1_codegen' (got 'RT')" in str(e.value)


def test_v1_register_type_no_inheritance_with_functional_api_roundtrip():
    @dataclass
    class Foo:
        b: bytes = b""
        s: str | None = None
        c: IPv4Address | None = None

    LoadMeta(v1=True).bind_to(Foo)

    register_type(Foo, IPv4Address)

    data = {"b": "AAAA", "c": "127.0.0.1", "s": "foobar"}

    foo = fromdict(Foo, data)
    assert foo.c == IPv4Address("127.0.0.1")

    assert asdict(foo) == data
    assert asdict(fromdict(Foo, asdict(foo))) == data


def test_v1_ipv4address_hooks_with_load_and_dump_mixins_roundtrip():
    @dataclass
    class Foo(JSONWizard, DumpMixin, LoadMixin):
        class Meta(JSONWizard.Meta):
            v1 = True

        c: IPv4Address | None = None

        @classmethod
        def load_to_ipv4_address(cls, tp: TypeInfo, extras: Extras) -> str:
            return tp.wrap(tp.v(), extras)

        @classmethod
        def dump_from_ipv4_address(cls, tp: TypeInfo, extras: Extras) -> str:
            return f"str({tp.v()})"

    Foo.register_load_hook(IPv4Address, Foo.load_to_ipv4_address)
    Foo.register_dump_hook(IPv4Address, Foo.dump_from_ipv4_address)

    data = {"c": "127.0.0.1"}

    foo = Foo.from_dict(data)
    assert foo.c == IPv4Address("127.0.0.1")

    assert foo.to_dict() == data
    assert Foo.from_dict(foo.to_dict()).to_dict() == data
