import pytest

from speccheck.main import summary
from speccheck.report import get_default_template_path


def test_summary():
    input_data = "tests/summary_test_baddict"
    output_file = "test_summary"
    with pytest.raises(ValueError, match="Sample ID mismatch"):
        summary(
            input_data,
            output_file,
            "species",
            "Sample",
            get_default_template_path(),
            plot=False,
        )
