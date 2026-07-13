"""QualiBact compatibility helpers.

The generic speccheck criteria engine is binary. This module provides a pinned
QualiBact ATB tier compatibility view for manuscript examples where WARN must
remain visible as a distinct tier.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

QUALIBACT_ECOLI_V1_SOURCE = (
    "https://static.qualibact.org/static/species/Escherichia_coli/qualibact-v1.0"
)
QUALIBACT_ECOLI_V1_LABEL = "QualiBact Escherichia_coli qualibact-v1.0 ATB tier logic"


@dataclass(frozen=True)
class TierThreshold:
    metric: str
    columns: tuple[str, ...]
    fail_lower: float | None = None
    fail_upper: float | None = None
    warn_lower: float | None = None
    warn_upper: float | None = None


ECOLI_V1_THRESHOLDS: tuple[TierThreshold, ...] = (
    TierThreshold(
        metric="N50",
        columns=("Quast.N50", "Checkm.N50 (scaffolds)", "Checkm.Contig_N50", "qualibact_N50"),
        fail_lower=20000.0,
    ),
    TierThreshold(
        metric="no_of_contigs",
        columns=(
            "Quast.# contigs (>= 0 bp)",
            "Checkm.# contigs",
            "Checkm.Total_Contigs",
            "qualibact_contigs",
        ),
        fail_upper=670.0,
        warn_upper=600.0,
    ),
    TierThreshold(
        metric="GC_Content",
        columns=("Quast.GC (%)", "Checkm.GC", "Checkm.GC_Content", "qualibact_gc_content"),
        warn_lower=50.25,
        warn_upper=50.88,
    ),
    TierThreshold(
        metric="Genome_Size",
        columns=(
            "Quast.Total length (>= 0 bp)",
            "Quast.Total length",
            "Checkm.Genome size (bp)",
            "Checkm.Genome_Size",
            "qualibact_genome_size",
        ),
        warn_lower=4400000.0,
        warn_upper=5700000.0,
    ),
    TierThreshold(
        metric="Total_Coding_Sequences",
        columns=("Checkm.Total_Coding_Sequences", "qualibact_total_coding_sequences"),
        warn_upper=5800.0,
    ),
)


def _first_numeric(row, columns):
    for column in columns:
        if column not in row:
            continue
        value = pd.to_numeric(pd.Series([row[column]]), errors="coerce").iloc[0]
        if pd.notna(value):
            return float(value)
    return None


def _format_threshold(value):
    numeric = float(value)
    if numeric.is_integer():
        return f"{numeric:.1f}"
    return f"{numeric:g}"


def _reason(metric, operator, threshold):
    return f"{metric} {operator}{_format_threshold(threshold)}"


def evaluate_ecoli_v1_row(row, warn_as_fail=False):
    """Return QualiBact-compatible tier fields for one E. coli row."""
    fail_reasons = []
    warn_reasons = []

    for threshold in ECOLI_V1_THRESHOLDS:
        value = _first_numeric(row, threshold.columns)
        if value is None:
            continue

        metric_failed = False
        if threshold.fail_lower is not None and value < threshold.fail_lower:
            fail_reasons.append(_reason(threshold.metric, "<", threshold.fail_lower))
            metric_failed = True
        if threshold.fail_upper is not None and value > threshold.fail_upper:
            fail_reasons.append(_reason(threshold.metric, ">", threshold.fail_upper))
            metric_failed = True

        if metric_failed:
            continue
        if threshold.warn_lower is not None and value < threshold.warn_lower:
            warn_reasons.append(_reason(threshold.metric, "<", threshold.warn_lower))
        if threshold.warn_upper is not None and value > threshold.warn_upper:
            warn_reasons.append(_reason(threshold.metric, ">", threshold.warn_upper))

    if fail_reasons:
        tier = "FAIL"
    elif warn_reasons:
        tier = "WARN"
    else:
        tier = "PASS"

    passed = tier == "PASS" or (tier == "WARN" and not warn_as_fail)
    reasons = fail_reasons + warn_reasons
    return {
        "qualibact_compat_tier": tier,
        "qualibact_compat_passed": passed,
        "qualibact_compat_reasons": "; ".join(reasons) or "none",
        "qualibact_compat_warn_policy": "warn-as-fail" if warn_as_fail else "warn-as-warn",
        "qualibact_compat_source": QUALIBACT_ECOLI_V1_LABEL,
    }


def add_qualibact_compatibility_columns(df, warn_as_fail=False):
    """Add pinned QualiBact E. coli v1 compatibility columns to a report dataframe."""
    if df.empty:
        return df
    rows = []
    for record in df.to_dict(orient="records"):
        record.update(evaluate_ecoli_v1_row(record, warn_as_fail=warn_as_fail))
        rows.append(record)
    return pd.DataFrame(rows)
