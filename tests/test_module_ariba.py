import pytest
import os
from speccheck.modules.ariba import Ariba


def test_has_valid_filename():
    ariba = Ariba("test_file.tsv")
    assert ariba.has_valid_filename

    ariba = Ariba("test_file.csv")
    assert not ariba.has_valid_filename

def test_ariba_has_not_valid_fileformat():
    ariba_file = "tests/collect_test_data/checkm.short.tsv"
    ariba = Ariba(ariba_file)
    assert not ariba.has_valid_fileformat

def test_ariba_has_valid_fileformat():
    ariba_file = "tests/collect_test_data/ariba_mlst_report.details.tsv"
    ariba = Ariba(ariba_file)
    assert ariba.has_valid_fileformat    

def test_aribavalues():
    ariba_file = "tests/collect_test_data/ariba_mlst_report.details.tsv"
    ariba = Ariba(ariba_file)
    values = ariba.fetch_values()
    assert values['passed'] == 4