import pytest
import os
from speccheck.modules.sylph import Sylph


def test_has_valid_filename():
    sylph = Sylph("test_file.tsv")
    assert sylph.has_valid_filename

    sylph = Sylph("test_file.csv")
    assert not sylph.has_valid_filename

def test_sylph_has_not_valid_fileformat():
    sylph_file = "tests/collect_test_data/checkm.short.tsv"
    sylph = Sylph(sylph_file)
    assert not sylph.has_valid_fileformat

def test_sylph_has_valid_fileformat():
    sylph_file = "tests/collect_test_data/sylph.tsv"
    sylph = Sylph(sylph_file)
    assert sylph.has_valid_fileformat

def test_sylphvalues():
    sylph_file = "tests/collect_test_data/sylph.tsv"
    sylph = Sylph(sylph_file)
    values = sylph.fetch_values()
    assert values['number_of_genomes'] == 2