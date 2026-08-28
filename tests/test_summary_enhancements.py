from pathlib import Path

import openpyxl
import pandas as pd
import pytest

from speccheck.main import summary
from speccheck.report import get_default_template_path
from speccheck.report_tables import (
    build_full_report_frame,
    build_large_run_summary_table,
    build_metric_summary_frames,
    build_species_metric_summary_frames,
    render_metric_summary_tables,
)


def _build_speccheck_summary_input(source_csv, destination):
    source = pd.read_csv(source_csv)
    records = []
    for _, row in source.iterrows():
        qc_pass = str(row["qc_verdict"]).lower() == "pass"
        n50_pass = str(row["N50_verdict"]).lower() == "pass"
        contig_pass = str(row["no_of_contigs_verdict"]).lower() == "pass"
        genome_pass = str(row["Genome_Size_verdict"]).lower() == "pass"
        checkm_pass = qc_pass and float(row["Contamination"]) <= 2.0
        records.append(
            {
                "sample_id": row["sample"],
                "speccheck_qc": "PASS" if qc_pass else "FAIL",
                "Checkm.qc_status": "PASS" if checkm_pass else "FAIL",
                "Checkm.Completeness": row["Completeness_Specific"],
                "Checkm.Contamination": row["Contamination"],
                "Checkm.GC_Content": row["GC_Content"],
                "Checkm.Genome_Size": row["Genome_Size"],
                "Checkm.Total_Contigs": row["number"],
                "Checkm.Contig_N50": row["N50"],
                "Checkm.Total_Coding_Sequences": row["Total_Coding_Sequences"],
                "Checkm.Completeness.status": "PASS",
                "Checkm.Contamination.status": (
                    "PASS" if float(row["Contamination"]) <= 2.0 else "FAIL"
                ),
                "Quast.qc_status": ("PASS" if n50_pass and contig_pass and genome_pass else "FAIL"),
                "Quast.N50": row["N50"],
                "Quast.N50.status": "PASS" if n50_pass else "FAIL",
                "Quast.# contigs (>= 0 bp)": row["number"],
                "Quast.# contigs (>= 0 bp).status": "PASS" if contig_pass else "FAIL",
                "Quast.Total length (>= 0 bp)": row["Genome_Size"],
                "Quast.Total length (>= 0 bp).status": "PASS" if genome_pass else "FAIL",
                "Quast.GC (%)": row["GC_Content"],
                "Quast.GC (%).status": (
                    "PASS" if str(row["GC_Content_verdict"]).lower() == "pass" else "FAIL"
                ),
                "Quast.Largest contig": row["longest"],
                "Speciator.qc_status": "PASS",
                "Speciator.speciesName": row["species_sylph"],
                "Speciator.confidence": "good",
                "Sylph.qc_status": "PASS",
                "Sylph.top_species": row["species_sylph"],
                "Sylph.top_abundance_percent": 95.0 if qc_pass else 75.0,
                "Sylph.number_of_genomes": 1,
            }
        )
    pd.DataFrame(records).to_csv(destination, index=False)


def test_summary_generates_interactive_html_and_xlsx(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    _build_speccheck_summary_input("tests/qualibact/ecoli_pass_subset.csv", input_dir / "pass.csv")
    _build_speccheck_summary_input("tests/qualibact/ecoli_fail_subset.csv", input_dir / "fail.csv")

    xlsx_output = output_dir / "report.xlsx"
    summary(
        str(input_dir),
        str(output_dir),
        "Speciator.speciesName",
        "sample_id",
        get_default_template_path(),
        plot=True,
        xlsx_output=str(xlsx_output),
        qualifyr_style=True,
    )

    report_html = (output_dir / "report.html").read_text(encoding="utf-8")
    assert (output_dir / "report.csv").exists()
    assert (output_dir / "report.html").exists()
    assert not (output_dir / "bulma.css").exists()
    assert xlsx_output.exists()
    assert "table-filter" in report_html
    assert "built-in qualifyr-style layout" in report_html
    assert "Speciator" in report_html
    assert "Species confidence" in report_html
    assert 'class="report-sidebar"' in report_html
    assert 'class="mobile-jump"' in report_html
    assert 'data-status-filter="NEEDS_REVIEW"' in report_html
    assert 'id="sample-detail-dialog"' in report_html
    assert 'class="tool-diagnostic"' in report_html
    assert 'id="metric-summary"' in report_html
    assert 'class="section-disclosure"' in report_html
    assert "setReviewStatus" in report_html
    assert "metricSpeciesFilter" in report_html
    assert "dialog.showModal()" in report_html
    assert "IntersectionObserver" in report_html
    assert "other.open = false" in report_html
    assert '<link rel="stylesheet" href="bulma.css">' not in report_html
    assert "<script src=" not in report_html
    assert "plotly.js v" not in report_html
    assert "Plotly" not in report_html
    assert 'class="inline-svg-chart' in report_html
    assert 'class="svg-data-point' in report_html
    assert 'raw === "PASSED"' not in report_html
    assert 'raw === "FAILED"' not in report_html
    assert ".report-header" in report_html

    workbook = openpyxl.load_workbook(xlsx_output)
    assert "report" in workbook.sheetnames
    assert "qc_status" in workbook.sheetnames

    concise = pd.read_csv(output_dir / "report.csv")
    full = pd.read_csv(output_dir / "report.full.csv")
    assert list(full.columns[: len(concise.columns)]) == list(concise.columns)
    assert list(concise.columns) == [
        "sample_id",
        "overall_qc",
        "speccheck_qc",
        "qualibact_qc",
        "historical_qualibact_qc",
        "reason_summary",
        "species",
        "species_confidence",
        "n50",
        "contigs",
        "genome_size",
        "gc_percent",
        "completeness",
        "contamination",
        "depth",
        "top_species",
        "top_abundance_percent",
        "threshold_source",
        "report_schema_version",
    ]
    assert set(concise["top_abundance_percent"]) == {75.0, 95.0}
    assert "all_checks_passed" not in full.columns
    assert "Checkm.GC_Content" in full.columns
    assert "Checkm.GC" not in full.columns
    assert "Checkm.Genome size (bp)" not in full.columns
    assert "Checkm.N50 (scaffolds)" not in full.columns
    assert "Checkm.# contigs" not in full.columns
    assert "Quast.Total length" not in full.columns
    status_columns = [
        column for column in full.columns if column.endswith(("_qc", ".qc_status", ".status"))
    ]
    observed_statuses = {
        str(value) for column in status_columns for value in full[column].dropna().unique()
    }
    assert observed_statuses <= {"PASS", "WARN", "FAIL", "NOT_EVALUATED"}


def test_summary_respects_no_interactive_tables(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    _build_speccheck_summary_input("tests/qualibact/ecoli_pass_subset.csv", input_dir / "pass.csv")

    summary(
        str(input_dir),
        str(output_dir),
        "Speciator.speciesName",
        "sample_id",
        get_default_template_path(),
        plot=True,
        interactive_tables=False,
        qualifyr_style=True,
    )

    report_html = (output_dir / "report.html").read_text(encoding="utf-8")
    assert 'class="table-filter"' not in report_html
    assert 'class="table report-table js-sort-filter"' not in report_html
    assert "parseValue" not in report_html
    assert '<link rel="stylesheet" href="bulma.css">' not in report_html


def test_html_escapes_parser_values(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    pd.DataFrame(
        [
            {
                "sample_id": '<script>alert("sample")</script>',
                "speccheck_qc": "PASS",
                "Speciator.qc_status": "PASS",
                "Speciator.speciesName": '<img src=x onerror=alert("species")>',
                "Speciator.confidence": "good",
            }
        ]
    ).to_csv(input_dir / "sample.csv", index=False)

    summary(
        str(input_dir),
        str(output_dir),
        "Speciator.speciesName",
        "sample_id",
        get_default_template_path(),
        plot=True,
    )
    report_html = (output_dir / "report.html").read_text(encoding="utf-8")
    assert '<script>alert("sample")</script>' not in report_html
    assert '<img src=x onerror=alert("species")>' not in report_html
    assert "&lt;script&gt;alert" in report_html
    assert "&lt;img src=x onerror=alert" in report_html


def test_summary_adds_qualibact_compatibility_columns(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    pd.DataFrame(
        [
            {
                "sample_id": "PASS1",
                "all_checks_passed": True,
                "Checkm.all_checks_passed": True,
                "Checkm.Completeness": 100,
                "Checkm.Contamination": 0.2,
                "Checkm.GC_Content": 50.5,
                "Checkm.GC.check": "PASS",
                "Checkm.Genome_Size": 5100000,
                "Checkm.Contig_N50": 120000,
                "Checkm.Total_Contigs": 200,
                "Quast.all_checks_passed": True,
                "Quast.N50": 120000,
                "Quast.# contigs (>= 0 bp)": 200,
                "Quast.GC (%)": 50.5,
                "Quast.Total length (>= 0 bp)": 5100000,
                "Quast.Largest contig": 500000,
                "Checkm.Total_Coding_Sequences": 4800,
                "Speciator.speciesName": "Escherichia coli",
                "Speciator.confidence": "good",
            },
            {
                "sample_id": "WARN1",
                "all_checks_passed": True,
                "Checkm.all_checks_passed": True,
                "Checkm.Completeness": 100,
                "Checkm.Contamination": 0.3,
                "Checkm.GC_Content": 50.4387,
                "Checkm.Genome_Size": 5695351,
                "Checkm.Contig_N50": 114262,
                "Checkm.Total_Contigs": 665,
                "Quast.all_checks_passed": True,
                "Quast.N50": 114262,
                "Quast.# contigs (>= 0 bp)": 665,
                "Quast.GC (%)": 50.4387,
                "Quast.Total length (>= 0 bp)": 5695351,
                "Quast.Largest contig": 297694,
                "Checkm.Total_Coding_Sequences": 6055,
                "Speciator.speciesName": "Escherichia coli",
                "Speciator.confidence": "good",
            },
            {
                "sample_id": "FAIL1",
                "all_checks_passed": True,
                "Checkm.all_checks_passed": True,
                "Checkm.Completeness": 100,
                "Checkm.Contamination": 0.4,
                "Checkm.GC_Content": 50.5585,
                "Checkm.Genome_Size": 5738641,
                "Checkm.Contig_N50": 126621,
                "Checkm.Total_Contigs": 679,
                "Quast.all_checks_passed": True,
                "Quast.N50": 126621,
                "Quast.# contigs (>= 0 bp)": 679,
                "Quast.GC (%)": 50.5585,
                "Quast.Total length (>= 0 bp)": 5738641,
                "Quast.Largest contig": 312707,
                "Checkm.Total_Coding_Sequences": 6105,
                "Speciator.speciesName": "Escherichia coli",
                "Speciator.confidence": "good",
            },
        ]
    ).to_csv(input_dir / "samples.csv", index=False)

    summary(
        str(input_dir),
        str(output_dir),
        "Speciator.speciesName",
        "sample_id",
        get_default_template_path(),
        plot=True,
        qualifyr_style=True,
        qualibact_compat=True,
    )

    report = pd.read_csv(output_dir / "report.csv")
    full = pd.read_csv(output_dir / "report.full.csv")
    tiers = dict(zip(report["sample_id"], report["qualibact_qc"], strict=False))
    overall = dict(zip(report["sample_id"], report["overall_qc"], strict=False))
    html = (output_dir / "report.html").read_text(encoding="utf-8")

    assert tiers == {"PASS1": "PASS", "WARN1": "WARN", "FAIL1": "FAIL"}
    assert overall == {"PASS1": "PASS", "WARN1": "WARN", "FAIL1": "FAIL"}
    assert "Checkm.GC_Content.status" in full.columns
    assert "Checkm.GC.status" not in full.columns
    assert full.columns.get_loc("Checkm.GC_Content.status") == (
        full.columns.get_loc("Checkm.GC_Content") + 1
    )
    assert "qualibact_qc" in html
    assert "Total_Coding_Sequences &gt;5800.0" in html


def test_historical_qualibact_label_does_not_override_current_qc(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    pd.DataFrame(
        [
            {
                "sample_id": "HISTORICAL_FAIL",
                "all_checks_passed": True,
                "qualibact_tier": "FAIL",
                "qualibact_reasons": "historical assembly failed",
            }
        ]
    ).to_csv(input_dir / "sample.csv", index=False)

    summary(
        str(input_dir),
        str(output_dir),
        "Speciator.speciesName",
        "sample_id",
        get_default_template_path(),
    )

    report = pd.read_csv(output_dir / "report.csv")
    assert report.loc[0, "overall_qc"] == "PASS"
    assert report.loc[0, "historical_qualibact_qc"] == "FAIL"
    assert report.loc[0, "reason_summary"] == "none"


def test_reason_summary_uses_canonical_metric_status(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    pd.DataFrame(
        [
            {
                "sample_id": "FAILED_GC",
                "speccheck_qc": "FAIL",
                "Checkm.GC_Content": 49.8,
                "Checkm.GC_Content.status": "FAIL",
            }
        ]
    ).to_csv(input_dir / "sample.csv", index=False)

    summary(
        str(input_dir),
        str(output_dir),
        "Speciator.speciesName",
        "sample_id",
        get_default_template_path(),
    )

    report = pd.read_csv(output_dir / "report.csv")
    assert report.loc[0, "reason_summary"] == "Checkm.GC_Content"


def test_summary_rejects_duplicate_sample_ids(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    pd.DataFrame(
        [
            {"sample_id": "S1", "all_checks_passed": True},
            {"sample_id": "S1", "all_checks_passed": False},
        ]
    ).to_csv(input_dir / "duplicates.csv", index=False)

    with pytest.raises(ValueError, match="duplicate sample IDs"):
        summary(
            str(input_dir),
            str(output_dir),
            "Speciator.speciesName",
            "sample_id",
            get_default_template_path(),
            plot=False,
        )


def test_summary_preserves_leading_zero_sample_ids(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    (input_dir / "samples.csv").write_text("sample_id,speccheck_qc\n00123,PASS\n", encoding="utf-8")

    summary(
        str(input_dir),
        str(output_dir),
        "Speciator.speciesName",
        "sample_id",
        get_default_template_path(),
    )

    assert (
        (output_dir / "report.csv").read_text(encoding="utf-8").splitlines()[1].startswith("00123,")
    )


def test_full_report_refuses_conflicting_alias_values():
    frame = pd.DataFrame([{"sample_id": "S1", "Checkm.GC": 50.1, "Checkm.GC_Content": 51.2}])
    with pytest.raises(ValueError, match="Cannot collapse report aliases"):
        build_full_report_frame(frame)


def test_cohort_metrics_offer_species_and_all_species_views():
    frame = pd.DataFrame(
        {
            "species": ["Escherichia coli", "Escherichia coli", "Shigella sonnei"],
            "Speciator.speciesName": [
                "Escherichia coli",
                "Escherichia coli",
                "Shigella sonnei",
            ],
            "Quast.N50": [100_000, 120_000, 30_000],
            "Checkm.Completeness": [100, 99, 97],
        }
    )

    species_summaries = build_species_metric_summary_frames(frame)
    html = render_metric_summary_tables(
        build_metric_summary_frames(frame),
        interactive_tables=True,
        species_summary_frames=species_summaries,
    )

    assert list(species_summaries) == ["Escherichia coli", "Shigella sonnei"]
    assert 'id="metric-species-filter"' in html
    assert "All species (3 samples)" in html
    assert "Escherichia coli (2 samples)" in html
    assert "Shigella sonnei (1 sample)" in html
    assert 'data-metric-species="all"' in html
    assert 'data-metric-species="species-2" hidden' in html


def test_thousand_sample_review_table_remains_paginated_and_compact():
    frame = pd.DataFrame(
        {
            "sample_id": [f"SAMPLE_{index:04d}" for index in range(1000)],
            "overall_qc": ["FAIL" if index < 10 else "PASS" for index in range(1000)],
            "speccheck_qc": ["FAIL" if index < 10 else "PASS" for index in range(1000)],
            "qualibact_qc": ["NOT_EVALUATED" if index < 5 else "PASS" for index in range(1000)],
            "historical_qualibact_qc": ["PASS"] * 1000,
            "reason_summary": [
                "Checkm.Completeness" if index < 10 else "none" for index in range(1000)
            ],
            "species": ["Escherichia coli"] * 1000,
            "Quast.N50": [100000] * 1000,
            "Quast.# contigs (>= 0 bp)": [100] * 1000,
        }
    )

    html = build_large_run_summary_table(frame, interactive_tables=True)

    assert 'data-page-size="25"' in html
    assert html.count('class="sample-review-row"') == 1000
    assert 'data-qc-status="FAIL"' in html
    assert 'data-qc-status="PASS"' in html
    assert "Historical QualiBact QC" not in html
    assert "Completeness</th>" not in html


def test_summary_rejects_missing_sample_column(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    pd.DataFrame([{"wrong_id": "S1", "all_checks_passed": True}]).to_csv(
        input_dir / "missing_sample.csv", index=False
    )

    with pytest.raises(ValueError, match="missing required sample column"):
        summary(
            str(input_dir),
            str(output_dir),
            "Speciator.speciesName",
            "sample_id",
            get_default_template_path(),
            plot=False,
        )


def test_summary_rejects_mismatched_embedded_sample_id(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    pd.DataFrame(
        [
            {
                "sample_id": "S1",
                "speccheck_qc": "PASS",
                "Speciator.Sample_id": "S2",
            }
        ]
    ).to_csv(input_dir / "mismatched_sample.csv", index=False)

    with pytest.raises(ValueError, match="Sample ID mismatch"):
        summary(
            str(input_dir),
            str(output_dir),
            "Speciator.speciesName",
            "sample_id",
            get_default_template_path(),
            plot=False,
        )


def test_summary_ignores_detailed_csv_and_output_directory(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = input_dir / "summary"
    input_dir.mkdir()
    pd.DataFrame([{"sample_id": "S1", "all_checks_passed": True}]).to_csv(
        input_dir / "sample.csv", index=False
    )
    pd.DataFrame([{"sample_id": "S1", "extra": "legacy"}]).to_csv(
        input_dir / "detailed.sample.csv", index=False
    )
    output_dir.mkdir()
    pd.DataFrame([{"sample_id": "S1", "old": "report"}]).to_csv(
        output_dir / "report.csv", index=False
    )

    summary(
        str(input_dir),
        str(output_dir),
        "Speciator.speciesName",
        "sample_id",
        get_default_template_path(),
        plot=False,
    )

    report = pd.read_csv(output_dir / "report.csv")
    assert list(report["sample_id"]) == ["S1"]
    assert "extra" not in report.columns
    assert "old" not in report.columns
