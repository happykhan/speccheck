import importlib
import os
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from speccheck.report import get_failure_reasons, load_modules_with_checks


@patch("os.listdir")
@patch("os.path.isfile")
@patch("importlib.util.spec_from_file_location")
@patch("importlib.util.module_from_spec")
def test_load_modules_with_checks(
    mock_module_from_spec, mock_spec_from_file_location, mock_isfile, mock_listdir
):
    pass


def test_get_failure_reasons_all_passed():
    """Regression test for issue #12: TypeError when all samples pass QC.

    When no samples fail, failure_reasons is an empty DataFrame and .sum()
    returns strings ('0') instead of integers, causing a TypeError on > 0.
    """
    df = pd.DataFrame(
        {
            "checkm.all_checks_passed": [True, True],
            "quast.all_checks_passed": [True, True],
            "speciator.all_checks_passed": [True, True],
        }
    )
    software_dict = {
        "checkm": {"name": "CheckM"},
        "quast": {"name": "Quast"},
        "speciator": {"name": "Speciator"},
    }
    # Should not raise TypeError
    result = get_failure_reasons(df, software_dict)
    assert isinstance(result, str)


def test_get_failure_reasons_does_not_duplicate_items():
    df = pd.DataFrame(
        {
            "Checkm.all_checks_passed": [False],
            "Quast.all_checks_passed": [True],
            "all_checks_passed": [False],
        }
    )
    software_dict = {
        "Checkm": {"name": "CheckM"},
        "Quast": {"name": "QUAST"},
    }

    result = get_failure_reasons(df, software_dict)

    assert result.count("<li>") == 1
    assert "CheckM" in result
