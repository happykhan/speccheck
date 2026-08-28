import csv

import pandas as pd

from speccheck.qualibact import (
    QUALIBACT_ECOLI_V1_LABEL,
    add_qualibact_compatibility_columns,
    evaluate_ecoli_v1_row,
    evaluate_qualibact_row,
)


def _row_from_fixture(path, index=0):
    with open(path, encoding="utf-8") as handle:
        row = list(csv.DictReader(handle))[index]
    return {
        "Quast.N50": row["N50"],
        "Quast.# contigs (>= 0 bp)": row["number"],
        "Quast.GC (%)": row["GC_Content"],
        "Quast.Total length (>= 0 bp)": row["Genome_Size"],
        "Checkm.Total_Coding_Sequences": row["Total_Coding_Sequences"],
    }


def test_qualibact_ecoli_v1_compatibility_reproduces_pass_warn_fail_tiers():
    pass_row = _row_from_fixture("tests/qualibact/ecoli_pass_subset.csv", 0)
    warn_row = {
        "Quast.N50": 114262,
        "Quast.# contigs (>= 0 bp)": 665,
        "Quast.GC (%)": 50.4387,
        "Quast.Total length (>= 0 bp)": 5695351,
        "Checkm.Total_Coding_Sequences": 6055,
    }
    fail_row = _row_from_fixture("tests/qualibact/ecoli_fail_subset.csv", 0)

    assert evaluate_ecoli_v1_row(pass_row)["qualibact_compat_tier"] == "PASS"

    warn_result = evaluate_ecoli_v1_row(warn_row)
    assert warn_result["qualibact_compat_tier"] == "WARN"
    assert "no_of_contigs >600.0" in warn_result["qualibact_compat_reasons"]
    assert "Total_Coding_Sequences >5800.0" in warn_result["qualibact_compat_reasons"]

    fail_result = evaluate_ecoli_v1_row(fail_row)
    assert fail_result["qualibact_compat_tier"] == "FAIL"
    assert "no_of_contigs >670.0" in fail_result["qualibact_compat_reasons"]


def test_qualibact_compatibility_uses_only_explicit_qc_statuses():
    row = _row_from_fixture("tests/qualibact/ecoli_pass_subset.csv")

    result = evaluate_ecoli_v1_row(row)

    assert result["qualibact_compat_tier"] == "PASS"
    assert "qualibact_compat_passed" not in result
    assert "qualibact_compat_warn_policy" not in result


def test_add_qualibact_columns_records_pinned_source():
    df = pd.DataFrame(
        [
            {
                "sample_id": "S1",
                "Quast.N50": 120000,
                "Quast.# contigs (>= 0 bp)": 200,
                "Quast.GC (%)": 50.5,
                "Quast.Total length (>= 0 bp)": 5100000,
                "Checkm.Total_Coding_Sequences": 4800,
            }
        ]
    )

    result = add_qualibact_compatibility_columns(df)

    assert result.loc[0, "qualibact_compat_tier"] == "PASS"
    assert result.loc[0, "qualibact_compat_source"] == QUALIBACT_ECOLI_V1_LABEL


def test_qualibact_boundaries_are_inclusive():
    final_boundary = {
        "Quast.N50": 20000,
        "Quast.# contigs (>= 0 bp)": 670,
        "Quast.GC (%)": 50.09,
        "Quast.Total length (>= 0 bp)": 4100000,
        "Checkm.Total_Coding_Sequences": 3900,
        "Checkm.Completeness": 95,
        "Checkm.Contamination": 16,
    }
    warn_boundary = {
        "Quast.N50": 23000,
        "Quast.# contigs (>= 0 bp)": 600,
        "Quast.GC (%)": 50.25,
        "Quast.Total length (>= 0 bp)": 4400000,
        "Checkm.Total_Coding_Sequences": 4200,
        "Checkm.Completeness": 100,
        "Checkm.Contamination": 2,
    }

    assert evaluate_ecoli_v1_row(final_boundary)["qualibact_compat_tier"] == "WARN"
    assert evaluate_ecoli_v1_row(warn_boundary)["qualibact_compat_tier"] == "PASS"

    outside = dict(final_boundary, **{"Quast.N50": 19999.99})
    assert evaluate_ecoli_v1_row(outside)["qualibact_compat_tier"] == "FAIL"


def test_shigella_assignments_use_ecoli_thresholds_without_changing_species():
    row = _row_from_fixture("tests/qualibact/ecoli_pass_subset.csv", 0)
    row["species"] = "Shigella flexneri"

    result = evaluate_qualibact_row(row)
    frame = add_qualibact_compatibility_columns(pd.DataFrame([row]))

    assert result["qualibact_compat_tier"] == "PASS"
    assert result["qualibact_compat_metrics_evaluated"] == 5
    assert result["qualibact_compat_source"] == (
        "Pinned QualiBact scheme for Escherichia coli (applied to Shigella flexneri)"
    )
    assert frame.loc[0, "species"] == "Shigella flexneri"


def test_species_without_scheme_or_alias_remain_not_evaluated():
    row = _row_from_fixture("tests/qualibact/ecoli_pass_subset.csv", 0)
    row["species"] = "Klebsiella imaginaryensis"

    result = evaluate_qualibact_row(row)

    assert result["qualibact_compat_tier"] == "NOT_EVALUATED"
    assert result["qualibact_compat_source"] == "not available"
