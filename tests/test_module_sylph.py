import os

import pytest

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
    assert values["number_of_genomes"] == 2
    assert values["top_abundance_percent"] == pytest.approx(67.9362)
    assert values["top_sequence_abundance_percent"] == pytest.approx(70.0042)
    assert values["taxonomic_abundances_percent"] == "67.9362;32.0638"
    assert "top_taxonomic_abundance" not in values


def test_sylph_accepts_reordered_headers_and_extra_columns(tmp_path):
    path = tmp_path / "sylph.tsv"
    path.write_text(
        "Genome_file\tExtra\tSequence_abundance\tSample_file\tAdjusted_ANI\t"
        "Contig_name\tTaxonomic_abundance\n"
        "GCF_1.fna\tignored\t99.2\treads.fastq.gz\t98.7\t"
        "NZ_1 Escherichia coli strain example\t100\n",
        encoding="utf-8",
    )
    sylph = Sylph(path)
    assert sylph.has_valid_fileformat
    assert sylph.fetch_values()["top_sequence_abundance_percent"] == pytest.approx(99.2)


@pytest.mark.parametrize("value", ["not-a-number", "-1", "101", "nan", "inf"])
def test_sylph_rejects_invalid_percentage(tmp_path, value):
    path = tmp_path / "sylph.tsv"
    path.write_text(
        "Sample_file\tGenome_file\tTaxonomic_abundance\tSequence_abundance\t"
        "Adjusted_ANI\tContig_name\n"
        f"reads.fastq.gz\tGCF_1.fna\t{value}\t99\t98.7\t"
        "NZ_1 Escherichia coli strain example\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="finite percentage|must be numeric"):
        Sylph(path).fetch_values()
