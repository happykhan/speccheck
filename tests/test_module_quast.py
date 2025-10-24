import os

import pytest

from speccheck.modules.quast import Quast


@pytest.fixture
def quast_file(tmp_path):
    data = """Assembly\tSampleAssembly
# contigs (>= 0 bp)\t100
# contigs (>= 1000 bp)\t80
# contigs (>= 5000 bp)\t60
# contigs (>= 10000 bp)\t40
# contigs (>= 25000 bp)\t20
# contigs (>= 50000 bp)\t10
Total length (>= 0 bp)\t3000000
Total length (>= 1000 bp)\t2500000
Total length (>= 5000 bp)\t2000000
Total length (>= 10000 bp)\t1500000
Total length (>= 25000 bp)\t1000000
Total length (>= 50000 bp)\t500000
# contigs\t100
Largest contig\t50000
Total length\t3000000
GC (%)\t50.5
N50\t25000
N90\t10000
auN\t20000.5
L50\t10
L90\t20
# N's per 100 kbp\t0.5
"""
    file_path = tmp_path / "report.tsv"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(data)
    return file_path


def test_fetch_values(quast_file):
    quast = Quast(quast_file)
    expected_values = {
        "Assembly": "SampleAssembly",
        "# contigs (>= 0 bp)": 100,
        "# contigs (>= 1000 bp)": 80,
        "# contigs (>= 5000 bp)": 60,
        "# contigs (>= 10000 bp)": 40,
        "# contigs (>= 25000 bp)": 20,
        "# contigs (>= 50000 bp)": 10,
        "Total length (>= 0 bp)": 3000000,
        "Total length (>= 1000 bp)": 2500000,
        "Total length (>= 5000 bp)": 2000000,
        "Total length (>= 10000 bp)": 1500000,
        "Total length (>= 25000 bp)": 1000000,
        "Total length (>= 50000 bp)": 500000,
        "# contigs": 100,
        "Largest contig": 50000,
        "Total length": 3000000,
        "GC (%)": 50.5,
        "N50": 25000,
        "N90": 10000,
        "auN": 20000.5,
        "L50": 10,
        "L90": 20,
        "# N's per 100 kbp": 0.5,
    }
    assert quast.fetch_values() == expected_values
