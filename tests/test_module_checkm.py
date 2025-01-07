import pytest
import os
from speccheck.modules.checkm import CheckM


def test_has_valid_filename():
    checkm = CheckM("test_file.tsv")
    assert checkm.has_valid_filename

    checkm = CheckM("test_file.csv")
    assert not checkm.has_valid_filename

def test_has_valid_fileformat():
    checkm_file = "tests/collect_test_data/checkm.short.tsv"
    checkm = CheckM(checkm_file)
    assert checkm.has_valid_fileformat

def test_checkmvalues():
    checkm_file = "tests/collect_test_data/checkm.short.tsv"
    checkm = CheckM(checkm_file)
    values = checkm.fetch_values()
    assert values['Marker lineage'] == 'Mycoplasma genitalium (6)'