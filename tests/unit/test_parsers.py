import pytest

from typing import Literal

from dataclass_wizard.parsers import LiteralParser


class TestLiteralParser:
    @pytest.fixture
    def literal_parser(self) -> LiteralParser:
        return LiteralParser(cls=object, base_type=Literal["foo"], extras={})

    def test_literal_parser_dunder_contains_succeeds_if_item_in_keys_of_base_type(self, literal_parser):
        assert "foo" in literal_parser

    def test_literal_parser_dunder_contains_fails_if_item_not_in_keys_of_base_type(self, literal_parser):
        assert "bar" not in literal_parser
