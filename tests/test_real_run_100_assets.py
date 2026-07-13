import json

import pandas as pd


def test_real_run_100_assets_are_internally_consistent():
    root = "examples/qualibact_ecoli/real_run_100"
    report = pd.read_csv(f"{root}/report/report.csv")
    cohort = pd.read_csv(f"{root}/cohort_accessions.csv")
    concordance = pd.read_csv(f"{root}/analysis/tier_concordance.csv", index_col=0)
    summary = json.loads(open(f"{root}/analysis/summary.json", encoding="utf-8").read())

    assert len(report) == report["sample_id"].nunique() == 100
    assert len(cohort) == cohort["sample_id"].nunique() == 100
    assert set(report["sample_id"]) == set(cohort["sample_id"])
    assert report["qualibact_tier"].value_counts().to_dict() == {
        "PASS": 70,
        "WARN": 20,
        "FAIL": 10,
    }
    assert report["qualibact_compat_tier"].value_counts().to_dict() == {
        "PASS": 85,
        "NOT_AVAILABLE": 7,
        "FAIL": 4,
        "WARN": 4,
    }
    assert int(concordance.to_numpy().sum()) == 100
    assert summary["exact_tier_agreement_count"] == 69
    assert summary["discordant_count"] == 31
