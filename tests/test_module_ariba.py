import os

import pytest

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
    assert values["passed"] == 4


def test_aribanull():
    ariba_file = "tests/collect_test_data/ariba_no_results.tsv"
    ariba = Ariba(ariba_file)
    values = ariba.fetch_values()
    assert values["percent"] == 0.0
    assert values["not_called"] == 7
    assert values["total"] == 7
    assert values["passed"] == 0


def test_ariba_header_only_file_has_zero_percent(tmp_path):
    path = tmp_path / "ariba.tsv"
    path.write_text("gene\tallele\tcov\tpc\tctgs\tdepth\thetmin\thets\n", encoding="utf-8")
    values = Ariba(path).fetch_values()
    assert values == {"passed": 0, "total": 0, "percent": 0.0, "not_called": 0}


def test_ariba_accepts_reordered_headers_and_extra_column(tmp_path):
    path = tmp_path / "ariba.tsv"
    path.write_text(
        "allele\tgene\tcov\tpc\tctgs\tdepth\thetmin\thets\textra\n"
        "1\tadk\t1\t100\t1\t30\t0\t0\tignored\n",
        encoding="utf-8",
    )
    parser = Ariba(path)
    assert parser.has_valid_fileformat
    assert parser.fetch_values()["percent"] == 100.0
