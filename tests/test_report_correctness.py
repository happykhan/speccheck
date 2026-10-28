"""Regression coverage for truthful, safe and accessible standalone reports."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from speccheck.plot_modules.plot_ariba import Plot_Ariba
from speccheck.plot_modules.plot_checkm import Plot_Checkm
from speccheck.plot_modules.plot_quast import Plot_Quast
from speccheck.plot_modules.plot_speciator import Plot_Speciator
from speccheck.plot_modules.plot_sylph import Plot_Sylph
from speccheck.report import build_report_context, plot_charts
from speccheck.report_tables import dataframe_to_interactive_table, tool_status_series
from speccheck.summary_workflow import decorate_report_dataframe, summary


@pytest.mark.parametrize("plotter", [Plot_Checkm, Plot_Quast, Plot_Sylph])
@pytest.mark.parametrize("status", ["WARN", "NOT_EVALUATED", "FAIL", "PASS"])
def test_tool_diagnostics_report_actual_status(plotter, status):
    frame = pd.DataFrame({"qc_status": [status]})
    html = plotter(frame).plot()
    assert f"1 {status.replace('_', ' ')}" in html
    assert "one or more samples failed" not in html
    assert "At least one sample failed" not in html


@pytest.mark.parametrize("plotter", [Plot_Checkm, Plot_Quast, Plot_Sylph, Plot_Ariba])
def test_tool_with_metrics_without_status_is_not_evaluated(plotter):
    html = plotter(pd.DataFrame({"metric": [1.5]})).plot()
    assert "1 NOT EVALUATED" in html or "1 not evaluated" in html
    assert "all samples passed" not in html


def test_missing_species_fields_are_reviewable():
    html = Plot_Speciator(pd.DataFrame({"confidence": ["poor"]}, index=["partial"])).plot()
    assert "Unknown" in html
    assert "NOT_EVALUATED" in html
    assert "partial" in html


def test_tool_statuses_include_metric_evidence_and_unknown_rows():
    frame = pd.DataFrame(
        {"qc_status": ["PASS", None, None], "metric.status": ["WARN", "FAIL", None]}
    )
    assert tool_status_series(frame).tolist() == ["WARN", "FAIL", "NOT_EVALUATED"]


def test_metric_names_cannot_inject_html():
    frame = pd.DataFrame({"<img src=x onerror=alert(1)>.status": ["WARN"]})
    html = Plot_Checkm(frame).plot()
    assert "<img src=x" not in html
    assert "&lt;img src=x" in html


def test_summary_without_native_status_uses_available_tool_evidence():
    frame = pd.DataFrame(
        {"sample_id": ["pass", "warn", "missing"], "Quast.qc_status": ["PASS", "WARN", None]}
    )
    decorated = decorate_report_dataframe(frame)
    assert decorated["overall_qc"].tolist() == ["PASS", "WARN", "NOT_EVALUATED"]


def test_report_context_agrees_across_counts_and_review_table():
    data = {
        "a": {"sample_id": "a", "Sylph.qc_status": "WARN"},
        "b": {"sample_id": "b", "Sylph.top_species": "Unknown"},
    }
    original = json.loads(json.dumps(data))
    context, frame, _ = build_report_context(data, "species")
    assert data == original
    assert frame.overall_qc.tolist() == ["WARN", "NOT_EVALUATED"]
    assert context["review_status_counts"]["NEEDS_REVIEW"] == 2
    assert 'data-qc-status="WARN"' in context["sample_review_table"]
    assert 'data-qc-status="NOT_EVALUATED"' in context["sample_review_table"]
    assert "1 warning" in context["sample_count"]


def test_empty_direct_report_is_valid(tmp_path):
    path = tmp_path / "empty.html"
    plot_charts({}, "species", output_html_path=path)
    html = path.read_text(encoding="utf-8")
    assert "0 of 0 samples require review" in html
    assert "No supported tool diagnostics were available" in html


def test_detail_json_cannot_close_script_and_retains_units(tmp_path):
    sample = "</script><img src=x onerror=alert(1)>"
    path = tmp_path / "report.html"
    plot_charts(
        {sample: {"sample_id": sample, "overall_qc": "WARN", "Checkm.Completeness": 98.2}},
        "species",
        output_html_path=path,
    )
    html = path.read_text(encoding="utf-8")
    payload = re.search(
        r'<script id="sample-details-data" type="application/json">(.*?)</script>', html, re.S
    ).group(1)
    assert "</script>" not in payload
    assert json.loads(payload)[sample]["metrics"] == [
        {"label": "Completeness (%)", "value": "98.20"}
    ]
    assert "<img src=x" not in html.replace(payload, "")


def test_sort_and_detail_controls_preserve_table_semantics():
    html = dataframe_to_interactive_table(
        pd.DataFrame({"Sample": ["safe"], "QC": ["PASS"]}),
        "test",
        row_id_column="Sample",
        clickable_rows=True,
    )
    assert '<th scope="col"' in html
    assert 'class="table-sort"' in html
    assert 'class="sample-open"' in html
    assert 'role="button"' not in html
    assert 'role="region" tabindex="0"' in html
    static = dataframe_to_interactive_table(
        pd.DataFrame({"Sample": ["safe"]}), "test", interactive=False
    )
    assert "<button" not in static


def test_static_report_has_no_nonfunctional_navigation_or_detail_prompts(tmp_path):
    path = tmp_path / "static.html"
    plot_charts(
        {"a": {"sample_id": "a", "overall_qc": "PASS"}},
        "species",
        output_html_path=path,
        interactive_tables=False,
    )
    html = path.read_text(encoding="utf-8")
    assert '<body class="static-report">' in html
    assert '<select id="report-jump">' not in html
    assert 'class="sidebar-toggle"' not in html
    assert "Select a row" not in html
    assert "Open a sample row" not in html


def test_metrics_only_summary_has_complete_not_evaluated_counts(tmp_path):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    pd.DataFrame(
        {"sample_id": ["partial"], "Checkm.Completeness": [98.2], "Speciator.confidence": ["poor"]}
    ).to_csv(inputs / "sample.csv", index=False)
    output = tmp_path / "output"
    summary(str(inputs), str(output), "Speciator.speciesName", "sample_id", None, plot=True)
    report = pd.read_csv(output / "report.csv")
    assert report.overall_qc.tolist() == ["NOT_EVALUATED"]
    assert "1 of 1 samples require review" in (output / "report.html").read_text(encoding="utf-8")


def test_table_interactions_execute_generated_script(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is required for the table interaction regression harness")
    path = tmp_path / "report.html"
    plot_charts({"a": {"sample_id": "a", "overall_qc": "PASS"}}, "species", output_html_path=path)
    harness = Path(__file__).with_name("report_interactions.cjs")
    result = subprocess.run(
        [node, str(harness), str(path)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_fallback_species_does_not_invent_a_speciator_run():
    context, frame, _ = build_report_context(
        {"a": {"sample_id": "a", "speccheck_qc": "WARN"}}, "Speciator.speciesName"
    )
    assert "Speciator.speciesName" not in frame
    assert context["software_navigation"] == []
    assert context["review_status_counts"]["WARN"] == 1


def test_explicit_missing_metric_status_is_not_replaced_by_legacy_boolean():
    frame = pd.DataFrame({"metric.status": ["NOT_EVALUATED"], "metric.check": [True]})
    assert tool_status_series(frame).tolist() == ["NOT_EVALUATED"]


def test_unrecognised_native_status_is_not_evaluated():
    frame = pd.DataFrame({"sample_id": ["a"], "speccheck_qc": ["unexpected"]})
    assert decorate_report_dataframe(frame).overall_qc.tolist() == ["NOT_EVALUATED"]


def test_queue_previews_escape_text_and_keep_full_reason():
    reason = "<img src=x onerror=alert(1)>" * 20
    html = dataframe_to_interactive_table(
        pd.DataFrame({"Reason summary": [reason]}), "preview", preview_columns=("Reason summary",)
    )
    assert 'class="cell-preview"' in html
    assert "<img src=x" not in html
    assert html.count("&lt;img src=x") == 40


def test_sample_details_include_legacy_failed_checks_once():
    context, _, _ = build_report_context(
        {"a": {"sample_id": "a", "Checkm.Completeness": 90, "Checkm.Completeness.check": False}},
        "species",
    )
    details = json.loads(context["sample_details_json"])
    assert details["a"]["checks"] == [{"label": "Checkm.Completeness", "value": "FAIL (90)"}]


def test_large_tables_have_compact_navigation_and_column_search():
    frame = pd.DataFrame({f"field_{i}": range(70) for i in range(20)})
    html = dataframe_to_interactive_table(frame, "wide", visible_columns=("field_0", "field_1"))
    assert 'data-page-size="10"' in html
    assert 'class="table-page-size"' in html
    assert 'class="table-page-number"' in html
    assert 'class="table-page-first"' in html
    assert 'class="table-page-last"' in html
    assert 'class="table-search-column"' in html
    assert 'class="table-columns"' in html
    assert html.count('class="table-column-toggle"') == 20
    assert 'value="2"  ' in html
    assert html.index('class="table-pagination"') < html.index("<table ")
    assert 'class="table-container table-scroll"' in html
    static = dataframe_to_interactive_table(frame, "static", interactive=False)
    assert 'class="table-column-toggle"' not in static
    assert 'class="table-search-column"' not in static
