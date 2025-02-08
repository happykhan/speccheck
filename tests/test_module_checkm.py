import pytest
import os
from speccheck.modules.checkm import Checkm


def test_has_valid_filename():
    checkm = Checkm("test_file.tsv")
    assert checkm.has_valid_filename

    checkm = Checkm("test_file.csv")
    assert not checkm.has_valid_filename

def test_has_valid_fileformat():
    checkm_file = "tests/collect_test_data/checkm.short.tsv"
    checkm = Checkm(checkm_file)
    assert checkm.has_valid_fileformat

def test_checkmvalues():
    checkm_file = "tests/collect_test_data/checkm.short.tsv"
    checkm = Checkm(checkm_file)
    values = checkm.fetch_values()
    assert values['Marker lineage'] == 'Mycoplasma genitalium (6)'