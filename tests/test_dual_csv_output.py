from speccheck.collect import write_to_file


def test_dual_csv_output_qc_like(tmp_path):
    """QC-like report should produce both concise and detailed CSVs.

    The concise CSV must have the fixed ordered header exactly as defined in
    collect.write_to_file, while the detailed CSV contains all keys in legacy
    ordering (we only assert its existence and a couple of representative fields).
    """
    output_file = tmp_path / "result.csv"

    qc_report = {
        # heuristic triggers: module-prefixed keys + sample_id + all_checks_passed
        "sample_id": "S1",
        "all_checks_passed": True,
        "Speciator.all_checks_passed": True,
        "Speciator.speciesName": "Escherichia coli",
        "Depth.all_checks_passed": True,
        "Depth.Depth": 45.7,
        "Depth.Read_type": "short",
        "Sylph.all_checks_passed": True,
        "Sylph.top_species": "Escherichia coli",
        "Sylph.top_taxonomic_abundance": 0.93,
        "Sylph.genomes": 1,
        "Quast.all_checks_passed": True,
        "Quast.# contigs (>= 0 bp).check": True,
        "Quast.# contigs": 120,
        "Quast.N50.check": True,
        "Quast.N50": 50000,
        "Quast.Total length (>= 0 bp).check": True,
        "Quast.Total length": 4800000,
        "Quast.GC (%).check": True,
        "Quast.GC (%)": 50.1,
        "Quast.Largest contig": 310000,
        "Checkm.all_checks_passed": True,
        "Checkm.Completeness.check": True,
        "Checkm.Completeness": 99.1,
        "Checkm.Contamination.check": True,
        "Checkm.Contamination": 0.4,
    }

    write_to_file(output_file, qc_report)

    concise_path = output_file
    detailed_path = output_file.parent / f"detailed.{output_file.name}"

    assert concise_path.exists(), "Concise output file missing"
    assert detailed_path.exists(), "Detailed output file missing"

    # Expected ordered columns (must match implementation in collect.write_to_file)
    expected_concise_columns = [
        "sample_id",
        "all_checks_passed",
        "Speciator.all_checks_passed",
        "Speciator.speciesName",
        "Depth.all_checks_passed",
        "Depth.Depth",
        "Depth.Read_type",
        "Sylph.all_checks_passed",
        "Sylph.top_species",
        "Sylph.top_taxonomic_abundance",
        "Quast.all_checks_passed",
        "Quast.# contigs (>= 0 bp).check",
        "Quast.# contigs",
        "Quast.N50.check",
        "Quast.N50",
        "Quast.Total length (>= 0 bp).check",
        "Quast.Total length",
        "Quast.GC (%).check",
        "Quast.GC (%)",
        "Quast.Largest contig",
        "Checkm.all_checks_passed",
        "Checkm.Completeness.check",
        "Checkm.Completeness",
        "Checkm.Contamination.check",
        "Checkm.Contamination",
        "Sylph.genomes",
    ]

    with open(concise_path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    assert lines[0] == ",".join(expected_concise_columns), "Concise header order mismatch"

    # Basic sanity checks for detailed file: contains representative keys
    with open(detailed_path, encoding="utf-8") as f_det:
        detailed_content = f_det.read()
    assert "Speciator.speciesName" in detailed_content
    assert "Quast.N50" in detailed_content
    assert "Checkm.Completeness" in detailed_content
