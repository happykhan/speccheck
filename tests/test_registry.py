import pytest

from speccheck.modules.base import Parser
from speccheck.registry import get_parser_classes


class ExampleParser(Parser):
    software_name = "ExampleParser"

    @property
    def has_valid_filename(self):
        return True

    @property
    def has_valid_fileformat(self):
        return True

    def fetch_values(self):
        return {"score": 1}


class DuplicateQuastParser(ExampleParser):
    software_name = "Quast"


class NotAParser:
    pass


class FakeEntryPoint:
    def __init__(self, name, loaded):
        self.name = name
        self.loaded = loaded

    def load(self):
        return self.loaded


@pytest.fixture(autouse=True)
def clear_parser_registry_cache():
    get_parser_classes.cache_clear()
    yield
    get_parser_classes.cache_clear()


def test_get_parser_classes_loads_valid_entry_point(monkeypatch):
    monkeypatch.setattr(
        "speccheck.registry.entry_points",
        lambda group: [FakeEntryPoint("example", ExampleParser)],
    )

    parsers = get_parser_classes()

    assert ExampleParser in parsers


def test_get_parser_classes_rejects_non_parser_entry_point(monkeypatch):
    monkeypatch.setattr(
        "speccheck.registry.entry_points",
        lambda group: [FakeEntryPoint("not_a_parser", NotAParser)],
    )

    with pytest.raises(TypeError, match="must load a Parser subclass"):
        get_parser_classes()


def test_get_parser_classes_rejects_duplicate_software_name(monkeypatch):
    monkeypatch.setattr(
        "speccheck.registry.entry_points",
        lambda group: [FakeEntryPoint("duplicate_quast", DuplicateQuastParser)],
    )

    with pytest.raises(ValueError, match="Duplicate Speccheck parser software name: Quast"):
        get_parser_classes()
