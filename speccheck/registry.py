"""Explicit runtime registries and canonical metric aliases.

The supported parser and plotting surface is deliberately small. Keeping it
explicit makes additions reviewable and avoids filename/class-name magic at
runtime. Metric equivalence groups provide one home for upstream and legacy
column names used by criteria, reports, and compatibility checks.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from functools import lru_cache
from importlib.metadata import entry_points

import pandas as pd

from speccheck.modules.ariba import Ariba
from speccheck.modules.base import Parser
from speccheck.modules.busco import Busco
from speccheck.modules.checkm import Checkm
from speccheck.modules.depth import Depth
from speccheck.modules.fastp import Fastp
from speccheck.modules.quast import Quast
from speccheck.modules.speciator import Speciator
from speccheck.modules.sylph import Sylph
from speccheck.plot_modules.plot_ariba import Plot_Ariba
from speccheck.plot_modules.plot_checkm import Plot_Checkm
from speccheck.plot_modules.plot_quast import Plot_Quast
from speccheck.plot_modules.plot_speciator import Plot_Speciator
from speccheck.plot_modules.plot_sylph import Plot_Sylph

PARSER_CLASSES = (Ariba, Busco, Checkm, Depth, Fastp, Quast, Speciator, Sylph)
PARSER_ENTRY_POINT_GROUP = "speccheck.parsers"

PLOT_CLASSES = {
    "Ariba": Plot_Ariba,
    "Checkm": Plot_Checkm,
    "Quast": Plot_Quast,
    "Speciator": Plot_Speciator,
    "Sylph": Plot_Sylph,
}

METRIC_EQUIVALENTS: Mapping[str, tuple[tuple[str, ...], ...]] = {
    "Checkm": (
        ("GC", "GC_Content"),
        ("Genome size (bp)", "Genome_Size"),
        ("N50 (scaffolds)", "Contig_N50"),
        ("# contigs", "Total_Contigs"),
    ),
}


@lru_cache(maxsize=1)
def get_parser_classes() -> tuple[type[Parser], ...]:
    """Return built-in parsers plus validated third-party entry points."""
    parsers: list[type[Parser]] = list(PARSER_CLASSES)
    names = {parser.software_name or parser.__name__ for parser in parsers}
    for entry_point in entry_points(group=PARSER_ENTRY_POINT_GROUP):
        parser = entry_point.load()
        if not isinstance(parser, type) or not issubclass(parser, Parser):
            raise TypeError(f"Parser entry point {entry_point.name!r} must load a Parser subclass")
        software_name = parser.software_name or parser.__name__
        if software_name in names:
            raise ValueError(f"Duplicate Speccheck parser software name: {software_name}")
        names.add(software_name)
        parsers.append(parser)
    return tuple(parsers)


def add_metric_aliases(values: MutableMapping, software: str) -> None:
    """Populate equivalent metric names from the first available value."""
    for equivalent_names in METRIC_EQUIVALENTS.get(software, ()):
        source = next((name for name in equivalent_names if name in values), None)
        if source is None:
            continue
        for alias in equivalent_names:
            values.setdefault(alias, values[source])


def add_frame_metric_aliases(frame: pd.DataFrame, software: str) -> pd.DataFrame:
    """Return a frame containing every registered equivalent metric column."""
    result = frame.copy()
    for equivalent_names in METRIC_EQUIVALENTS.get(software, ()):
        source = next((name for name in equivalent_names if name in result.columns), None)
        if source is None:
            continue
        for alias in equivalent_names:
            if alias not in result.columns:
                result[alias] = result[source]
    return result
