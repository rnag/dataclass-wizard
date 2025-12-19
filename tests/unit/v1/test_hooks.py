from __future__ import annotations

from dataclasses import dataclass
from ipaddress import IPv4Address

from dataclass_wizard import JSONWizard
from dataclass_wizard.v1 import DumpMixin, LoadMixin
from dataclass_wizard.v1.models import TypeInfo, Extras


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
