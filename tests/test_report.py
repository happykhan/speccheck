import os
import importlib
import pytest
from unittest.mock import patch, MagicMock
from speccheck.report import load_modules_with_checks


@patch("os.listdir")
@patch("os.path.isfile")
@patch("importlib.util.spec_from_file_location")
@patch("importlib.util.module_from_spec")
def test_load_modules_with_checks(
    mock_module_from_spec, mock_spec_from_file_location, mock_isfile, mock_listdir
):
    pass
