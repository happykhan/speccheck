import pytest
import os
from speccheck.modules.checkm import CheckM

def test_has_valid_filename():
    checkm = CheckM("test_file.tsv")
    assert checkm.has_valid_filename == True

    checkm = CheckM("test_file.csv")
    assert checkm.has_valid_filename == False

