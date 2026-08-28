import pandas as pd

from speccheck.plot_modules.svg_charts import (
    render_scatter_chart,
    render_species_bar_chart,
)


def test_species_bar_chart_is_accessible_and_escapes_labels():
    status_counts = pd.DataFrame(
        {"PASS": [3, 0], "FAIL": [0, 1]},
        index=["Escherichia coli", '<script>alert("x")</script>'],
    )
    html = render_species_bar_chart(
        pd.Series([3, 1], index=["Escherichia coli", '<script>alert("x")</script>']),
        title="Species distribution",
        status_counts=status_counts,
    )

    assert 'class="inline-svg-chart species-bar-chart"' in html
    assert 'role="img"' in html
    assert "Escherichia coli | PASS: 3 sample(s)" in html
    assert "3</strong> PASS" in html
    assert "1</strong> FAIL" in html
    assert 'class="svg-bar qc-bar-pass"' in html
    assert 'class="svg-bar qc-bar-fail"' in html
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_scatter_chart_has_qc_hover_and_sample_detail_hooks():
    frame = pd.DataFrame(
        {
            "sample_id": ["sample-1", '<sample id="2">', "sample-3", "sample-4"],
            "species": ["Escherichia coli"] * 4,
            "qc_status": ["PASS", "FAIL", "WARN", "NOT_EVALUATED"],
            "x": [0.5, 1.5, 1.0, 2.0],
            "y": [98.2, 91.4, 95.0, 93.0],
        }
    )

    html = render_scatter_chart(
        frame,
        x_column="x",
        y_column="y",
        x_label="Contamination (%)",
        y_label="Completeness (%)",
        title="Contamination vs completeness",
    )

    assert html.count('class="svg-data-point') == 4
    assert '<circle class="svg-data-point qc-point-pass"' in html
    assert '<polygon class="svg-data-point qc-point-warn"' in html
    assert '<polygon class="svg-data-point qc-point-fail"' in html
    assert '<rect class="svg-data-point qc-point-not-evaluated"' in html
    assert 'data-qc-status="NOT_EVALUATED"' in html
    assert 'data-sample-id="sample-1"' in html
    assert 'data-sample-id="&lt;sample id=&quot;2&quot;&gt;"' in html
    assert "QC: FAIL" in html
    assert html.count("1</strong>") == 4
    assert 'tabindex="0" role="button"' in html
    assert "Select a point to open the sample details" in html


def test_scatter_chart_handles_missing_or_non_finite_metrics():
    missing = render_scatter_chart(
        pd.DataFrame({"x": [1]}),
        x_column="x",
        y_column="y",
        x_label="X",
        y_label="Y",
        title="Missing",
    )
    non_finite = render_scatter_chart(
        pd.DataFrame({"x": [float("inf")], "y": [float("nan")]}),
        x_column="x",
        y_column="y",
        x_label="X",
        y_label="Y",
        title="Non-finite",
    )

    assert "required for this chart were unavailable" in missing
    assert "No finite values were available" in non_finite
