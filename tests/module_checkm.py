import pytest
import os
from speccheck.modules.checkm import CheckM

def test_has_valid_filename():
    checkm = CheckM("test_file.tsv")
    assert checkm.has_valid_filename == True

    checkm = CheckM("test_file.csv")
    assert checkm.has_valid_filename == False

def test_has_valid_fileformat_valid():
    valid_file = "valid_checkm.tsv"
    with open(valid_file, "w", encoding="utf-8") as f:
        f.write("Bin Id\tMarker lineage\t# genomes\t# markers\t# marker sets\tCompleteness\tContamination\tStrain heterogeneity\tGenome size (bp)\t# ambiguous bases\t# scaffolds\t# contigs\tN50 (scaffolds)\tN50 (contigs)\tMean scaffold length (bp)\tMean contig length (bp)\tLongest scaffold (bp)\tLongest contig (bp)\tGC\tGC std (scaffolds > 1kbp)\tCoding density\tTranslation table\t# predicted genes\t0\t1\t2\t3\t4\t5+\n")
        f.write("bin1\tlineage1\t1\t1\t1\t99.9\t0.1\t0.0\t1000000\t0\t1\t1\t500000\t500000\t500000\t500000\t500000\t500000\t50.0\t0.0\t90.0\t11\t1000\t0\t0\t0\t0\t0\t0\n")

    checkm = CheckM(valid_file)
    assert checkm.has_valid_fileformat == True
    os.remove(valid_file)

def test_has_valid_fileformat_invalid():
    invalid_file = "invalid_checkm.tsv"
    with open(invalid_file, "w", encoding="utf-8") as f:
        f.write("Invalid header\n")
        f.write("invalid data\n")

    checkm = CheckM(invalid_file)
    assert checkm.has_valid_fileformat == False
    os.remove(invalid_file)

def test_fetch_values_valid():
    valid_file = "valid_checkm.tsv"
    with open(valid_file, "w", encoding="utf-8") as f:
        f.write("Bin Id\tMarker lineage\t# genomes\t# markers\t# marker sets\tCompleteness\tContamination\tStrain heterogeneity\tGenome size (bp)\t# ambiguous bases\t# scaffolds\t# contigs\tN50 (scaffolds)\tN50 (contigs)\tMean scaffold length (bp)\tMean contig length (bp)\tLongest scaffold (bp)\tLongest contig (bp)\tGC\tGC std (scaffolds > 1kbp)\tCoding density\tTranslation table\t# predicted genes\t0\t1\t2\t3\t4\t5+\n")
        f.write("bin1\tlineage1\t1\t1\t1\t99.9\t0.1\t0.0\t1000000\t0\t1\t1\t500000\t500000\t500000\t500000\t500000\t500000\t50.0\t0.0\t90.0\t11\t1000\t0\t0\t0\t0\t0\t0\n")

    checkm = CheckM(valid_file)
    expected_output = {
        'Bin Id': 'bin1',
        'Marker lineage': 'lineage1',
        '# genomes': 1,
        '# markers': 1,
        '# marker sets': 1,
        'Completeness': 99.9,
        'Contamination': 0.1,
        'Strain heterogeneity': 0.0,
        'Genome size (bp)': 1000000,
        '# ambiguous bases': 0,
        '# scaffolds': 1,
        '# contigs': 1,
        'N50 (scaffolds)': 500000,
        'N50 (contigs)': 500000,
        'Mean scaffold length (bp)': 500000,
        'Mean contig length (bp)': 500000,
        'Longest scaffold (bp)': 500000,
        'Longest contig (bp)': 500000,
        'GC': 50.0,
        'GC std (scaffolds > 1kbp)': 0.0,
        'Coding density': 90.0,
        'Translation table': 11,
        '# predicted genes': 1000,
        '0': 0,
        '1': 0,
        '2': 0,
        '3': 0,
        '4': 0,
        '5+': 0
    }
    assert checkm.fetch_values() == expected_output
    os.remove(valid_file)

def test_fetch_values_invalid():
    invalid_file = "invalid_checkm.tsv"
    with open(invalid_file, "w", encoding="utf-8") as f:
        f.write("Bin Id\tMarker lineage\t# genomes\t# markers\t# marker sets\tCompleteness\tContamination\tStrain heterogeneity\tGenome size (bp)\t# ambiguous bases\t# scaffolds\t# contigs\tN50 (scaffolds)\tN50 (contigs)\tMean scaffold length (bp)\tMean contig length (bp)\tLongest scaffold (bp)\tLongest contig (bp)\tGC\tGC std (scaffolds > 1kbp)\tCoding density\tTranslation table\t# predicted genes\t0\t1\t2\t3\t4\t5+\n")
        f.write("bin1\tlineage1\t1\t1\t1\t99.9\t0.1\t0.0\t1000000\t0\t1\t1\t500000\t500000\t500000\t500000\t500000\t500000\t50.0\t0.0\t90.0\t11\t1000\t0\t0\t0\t0\t0\t0\n")
        f.write("bin2\tlineage2\t1\t1\t1\t99.9\t0.1\t0.0\t1000000\t0\t1\t1\t500000\t500000\t500000\t500000\t500000\t500000\t50.0\t0.0\t90.0\t11\t1000\t0\t0\t0\t0\t0\t0\n")

    checkm = CheckM(invalid_file)
    with pytest.raises(ValueError, match="The file must contain exactly one row of values."):
        checkm.fetch_values()
    os.remove(invalid_file)