import json
from pathlib import Path

import pandas as pd


def test_real_run_100_assets_are_internally_consistent():
    root = "examples/qualibact_ecoli/real_run_100"
    report = pd.read_csv(f"{root}/report/report.csv")
    cohort = pd.read_csv(f"{root}/cohort_accessions.csv")
    concordance = pd.read_csv(f"{root}/analysis/tier_concordance.csv", index_col=0)
    summary = json.loads(open(f"{root}/analysis/summary.json", encoding="utf-8").read())
    report_html_path = Path(root) / "report" / "report.html"
    report_html = report_html_path.read_text(encoding="utf-8")

    assert len(report) == report["sample_id"].nunique() == 100
    assert len(cohort) == cohort["sample_id"].nunique() == 100
    assert set(report["sample_id"]) == set(cohort["sample_id"])
    assert report["historical_qualibact_qc"].value_counts().to_dict() == {
        "PASS": 70,
        "WARN": 20,
        "FAIL": 10,
    }
    assert report["qualibact_qc"].value_counts().to_dict() == {
        "PASS": 89,
        "FAIL": 4,
        "WARN": 4,
        "NOT_EVALUATED": 3,
    }
    shigella = report[report["species"].str.startswith("Shigella ")]
    assert len(shigella) == 4
    assert set(shigella["qualibact_qc"]) == {"PASS"}
    assert int(concordance.to_numpy().sum()) == 100
    assert summary["exact_tier_agreement_count"] == 73
    assert summary["discordant_count"] == 27
    assert report_html_path.stat().st_size < 1_000_000
    assert "plotly.js" not in report_html.lower()
    assert report_html.count('class="inline-svg-chart') == 3
    assert "QualiBact threshold source" in report_html
    assert "applied to Shigella flexneri" in report_html
