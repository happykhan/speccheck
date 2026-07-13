import pandas as pd

from speccheck.plot_modules.plot_ariba import Plot_Ariba


def test_plot_ariba_renders_empty_table_without_summary_counts():
    html = Plot_Ariba(pd.DataFrame()).plot()

    assert '<section class="software-block">' in html
    assert "<h2 id=\"ariba\">ARIBA</h2>" in html
    assert "<th>Sample</th>" in html
    assert "<strong>Summary:</strong>" not in html


def test_plot_ariba_renders_rows_statuses_and_summary_counts():
    frame = pd.DataFrame(
        {
            "species": ["Escherichia coli", "Escherichia coli"],
            "passed": [4, 2],
            "total": [4, 4],
            "percent": [100.0, 50.0],
            "percent.check": [True, False],
            "all_checks_passed": [True, False],
        },
        index=["SAMPLE_PASS", "SAMPLE_FAIL"],
    )

    html = Plot_Ariba(frame).plot()

    assert "SAMPLE_PASS" in html
    assert "SAMPLE_FAIL" in html
    assert "100.0%" in html
    assert "50.0%" in html
    assert '<span class="qc-pass">PASSED</span>' in html
    assert '<span class="qc-fail">FAILED</span>' in html
    assert "2 samples" in html
    assert "1 passed" in html
    assert "1 failed" in html
