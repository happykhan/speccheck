import csv

import pandas as pd

from speccheck.qualibact import (
    QUALIBACT_ECOLI_V1_LABEL,
    add_qualibact_compatibility_columns,
    evaluate_ecoli_v1_row,
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
    assert warn_result["qualibact_compat_passed"] is True
    assert "no_of_contigs >600.0" in warn_result["qualibact_compat_reasons"]
    assert "Total_Coding_Sequences >5800.0" in warn_result["qualibact_compat_reasons"]

    fail_result = evaluate_ecoli_v1_row(fail_row)
    assert fail_result["qualibact_compat_tier"] == "FAIL"
    assert fail_result["qualibact_compat_passed"] is False
    assert "no_of_contigs >670.0" in fail_result["qualibact_compat_reasons"]


def test_qualibact_warn_as_fail_policy_changes_passed_not_tier():
    warn_row = {
        "Quast.N50": 114262,
        "Quast.# contigs (>= 0 bp)": 665,
        "Quast.GC (%)": 50.4387,
        "Quast.Total length (>= 0 bp)": 5695351,
        "Checkm.Total_Coding_Sequences": 6055,
    }

    result = evaluate_ecoli_v1_row(warn_row, warn_as_fail=True)

    assert result["qualibact_compat_tier"] == "WARN"
    assert result["qualibact_compat_passed"] is False
    assert result["qualibact_compat_warn_policy"] == "warn-as-fail"


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
