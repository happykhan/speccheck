import os

import pytest

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
    assert values["Completeness"] == 93.2


def test_checkm_gc_fraction_is_normalized_to_percent(tmp_path):
    checkm_file = tmp_path / "checkm.tsv"
    checkm_file.write_text(
        "\t".join(
            [
                "Name",
                "Completeness",
                "Contamination",
                "Completeness_Model_Used",
                "Translation_Table_Used",
                "Coding_Density",
                "Contig_N50",
                "Average_Gene_Length",
                "Genome_Size",
                "GC_Content",
                "Total_Coding_Sequences",
                "Total_Contigs",
                "Max_Contig_Length",
                "Additional_Notes",
            ]
        )
        + "\n"
        + "\t".join(
            [
                "sample",
                "100.0",
                "0.1",
                "NN",
                "11",
                "0.9",
                "120000",
                "300",
                "5000000",
                "0.51",
                "5000",
                "120",
                "300000",
                "None",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    values = Checkm(str(checkm_file)).fetch_values()

    assert values["GC_Content"] == pytest.approx(51.0)
