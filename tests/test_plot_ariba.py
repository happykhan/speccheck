import pandas as pd

from speccheck.plot_modules.plot_ariba import Plot_Ariba


def test_plot_ariba_renders_empty_state_without_summary_counts():
    html = Plot_Ariba(pd.DataFrame()).plot()

    assert '<section class="software-block">' in html
    assert '<h2 id="ariba">ARIBA</h2>' in html
    assert "No ARIBA results were available." in html
    assert "<strong>Summary:</strong>" not in html


def test_plot_ariba_renders_only_exception_rows_and_summary_counts():
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

    assert "SAMPLE_PASS" not in html
    assert "SAMPLE_FAIL" in html
    assert "100.0%" not in html
    assert "50" in html
    assert 'class="qc-fail">FAIL</td>' in html
    assert "ARIBA exceptions require review" in html
    assert "2 samples" in html
    assert "1 passed" in html
    assert "1 failed" in html
