"""Generic PASS/WARN/FAIL evaluation from a pinned QualiBact snapshot."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from speccheck.update_criteria import QUALIBACT_SNAPSHOT_PATH

QUALIBACT_ECOLI_V1_SOURCE = (
    "https://static.qualibact.org/static/species/Escherichia_coli/qualibact-v1.0"
)
QUALIBACT_ECOLI_V1_LABEL = "QualiBact Escherichia coli qualibact-v1.0"

METRIC_COLUMNS = {
    "N50": (
        "Quast.N50",
        "Checkm.N50 (scaffolds)",
        "Checkm.Contig_N50",
        "qualibact_N50",
    ),
    "no_of_contigs": (
        "Quast.# contigs (>= 0 bp)",
        "Checkm.# contigs",
        "Checkm.Total_Contigs",
        "qualibact_contigs",
    ),
    "GC_Content": (
        "Quast.GC (%)",
        "Checkm.GC",
        "Checkm.GC_Content",
        "qualibact_gc_content",
    ),
    "Genome_Size": (
        "Quast.Total length (>= 0 bp)",
        "Quast.Total length",
        "Checkm.Genome size (bp)",
        "Checkm.Genome_Size",
        "qualibact_genome_size",
    ),
    "Total_Coding_Sequences": (
        "Checkm.Total_Coding_Sequences",
        "qualibact_total_coding_sequences",
    ),
    "Completeness": ("Checkm.Completeness", "qualibact_completeness"),
    "Completeness_Specific": ("Checkm.Completeness", "qualibact_completeness"),
    "Contamination": ("Checkm.Contamination", "qualibact_contamination"),
    "longest": ("Quast.Largest contig", "Checkm.Max_Contig_Length"),
}


@dataclass(frozen=True)
class TierThreshold:
    metric: str
    columns: tuple[str, ...]
    fail_lower: float | None = None
    fail_upper: float | None = None
    warn_lower: float | None = None
    warn_upper: float | None = None


def _number(value):
    if value in (None, ""):
        return None
    return float(value)


@lru_cache(maxsize=1)
def load_thresholds() -> dict[str, tuple[TierThreshold, ...]]:
    """Load the packaged, release-pinned QualiBact threshold snapshot."""
    grouped: dict[str, list[TierThreshold]] = {}
    with open(QUALIBACT_SNAPSHOT_PATH, encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            columns = METRIC_COLUMNS.get(row["metric"])
            if columns is None:
                continue
            fail_lower = _number(row.get("FINAL_lower"))
            fail_upper = _number(row.get("FINAL_upper"))
            grouped.setdefault(row["species"], []).append(
                TierThreshold(
                    metric=row["metric"],
                    columns=columns,
                    fail_lower=fail_lower,
                    fail_upper=fail_upper,
                    # QualiBact suppresses a WARN side when no FAIL side exists.
                    warn_lower=_number(row.get("WARN_lower")) if fail_lower is not None else None,
                    warn_upper=_number(row.get("WARN_upper")) if fail_upper is not None else None,
                )
            )
    return {species: tuple(rows) for species, rows in grouped.items()}


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


def _row_species(row, explicit_species=None):
    if explicit_species:
        return explicit_species
    for column in ("species", "Speciator.speciesName", "organism"):
        value = row.get(column)
        if value and str(value).lower() != "nan":
            return str(value)
    return None


def evaluate_qualibact_row(row, *, species=None, warn_as_fail=False):
    """Evaluate one row against its species' pinned QualiBact scheme."""
    resolved_species = _row_species(row, species)
    thresholds = load_thresholds().get(resolved_species, ())
    if not thresholds:
        return {
            "qualibact_compat_tier": "NOT_AVAILABLE",
            "qualibact_compat_passed": "NOT_AVAILABLE",
            "qualibact_compat_reasons": "No pinned QualiBact scheme for species",
            "qualibact_compat_warn_policy": ("warn-as-fail" if warn_as_fail else "warn-as-warn"),
            "qualibact_compat_source": "not available",
            "qualibact_compat_metrics_evaluated": 0,
            "qualibact_compat_metrics_missing": 0,
        }

    fail_reasons = []
    warn_reasons = []
    evaluated = 0
    missing = 0
    for threshold in thresholds:
        value = _first_numeric(row, threshold.columns)
        if value is None:
            missing += 1
            continue
        evaluated += 1
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

    if not evaluated:
        tier = "NOT_EVALUATED"
        passed = "NOT_EVALUATED"
        reasons = "No matching metrics were available"
    else:
        tier = "FAIL" if fail_reasons else "WARN" if warn_reasons else "PASS"
        passed = tier == "PASS" or (tier == "WARN" and not warn_as_fail)
        reasons = "; ".join(fail_reasons + warn_reasons) or "none"
    return {
        "qualibact_compat_tier": tier,
        "qualibact_compat_passed": passed,
        "qualibact_compat_reasons": reasons,
        "qualibact_compat_warn_policy": "warn-as-fail" if warn_as_fail else "warn-as-warn",
        "qualibact_compat_source": f"Pinned QualiBact scheme for {resolved_species}",
        "qualibact_compat_metrics_evaluated": evaluated,
        "qualibact_compat_metrics_missing": missing,
    }


def evaluate_ecoli_v1_row(row, warn_as_fail=False):
    """Backward-compatible E. coli v1 evaluator."""
    result = evaluate_qualibact_row(row, species="Escherichia coli", warn_as_fail=warn_as_fail)
    result["qualibact_compat_source"] = QUALIBACT_ECOLI_V1_LABEL
    return result


def add_qualibact_compatibility_columns(df, warn_as_fail=False):
    """Add QualiBact compatibility columns to a report frame.

    Historical report tables did not carry a species column and were explicitly
    E. coli-only. Preserve that behaviour while using species-aware thresholds
    whenever a species value is present.
    """
    if df.empty:
        return df
    rows = []
    for record in df.to_dict(orient="records"):
        if _row_species(record) is None:
            result = evaluate_ecoli_v1_row(record, warn_as_fail=warn_as_fail)
        else:
            result = evaluate_qualibact_row(record, warn_as_fail=warn_as_fail)
        record.update(result)
        rows.append(record)
    return pd.DataFrame(rows)
