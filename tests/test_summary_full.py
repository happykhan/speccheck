import os
from speccheck.main import summary
import csv


def test_summary():
    input_data = "tests/summary_test_baddict"
    output_file = "test_summary"
    summary(input_data, output_file, "species", "Sample", "templates/report.html", plot=False)

    # Check if the output file is created
    output_file += ".csv"
