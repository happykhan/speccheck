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
        "Speciator.confidence": "good",
        "Depth.all_checks_passed": True,
        "Depth.Depth": 45.7,
        "Depth.Read_type": "short",
        "Sylph.all_checks_passed": True,
        "Sylph.top_species": "Escherichia coli",
        "Sylph.top_abundance_percent": 93.0,
        "Sylph.top_sequence_abundance_percent": 99.5,
        "Sylph.top_adjusted_ani": 99.8,
        "Sylph.number_of_genomes": 1,
        "Sylph.species_name": "Escherichia coli",
        "Sylph.taxonomic_abundances_percent": "93.0",
        "Sylph.sequence_abundances_percent": "99.5",
        "Sylph.genomes": 1,
        "Quast.all_checks_passed": True,
        "Quast.# contigs (>= 0 bp).check": True,
        "Quast.# contigs (>= 0 bp)": 120,
        "Quast.# contigs": 120,
        "Quast.N50.check": True,
        "Quast.N50": 50000,
        "Quast.Total length (>= 0 bp).check": True,
        "Quast.Total length (>= 0 bp)": 4800000,
        "Quast.Total length": 4800000,
        "Quast.GC (%).check": True,
        "Quast.GC (%)": 50.1,
        "Quast.Largest contig": 310000,
        "Checkm.all_checks_passed": True,
        "Checkm.Completeness.check": True,
        "Checkm.Completeness": 99.1,
        "Checkm.Contamination.check": True,
        "Checkm.Contamination": 0.4,
        "Checkm.GC_Content": 50.1,
        "Checkm.Genome_Size": 4800000,
        "Checkm.Contig_N50": 50000,
        "Checkm.Total_Contigs": 120,
        "Checkm.Total_Coding_Sequences": 4700,
        "Ariba.qc_status": "PASS",
        "Ariba.percent.status": "PASS",
        "Ariba.percent": 100.0,
        "Ariba.passed": 7,
        "Ariba.total": 7,
        "Ariba.not_called": 0,
        "qualibact_tier": "PASS",
    }

    write_to_file(output_file, qc_report)

    concise_path = output_file
    detailed_path = output_file.parent / f"detailed.{output_file.name}"

    assert concise_path.exists(), "Concise output file missing"
    assert detailed_path.exists(), "Detailed output file missing"

    # Expected ordered columns (must match implementation in collect.write_to_file)
    expected_concise_columns = [
        "sample_id",
        "speccheck_qc",
        "Speciator.qc_status",
        "Speciator.speciesName",
        "Speciator.confidence",
        "Depth.qc_status",
        "Depth.Depth",
        "Depth.Read_type",
        "Sylph.qc_status",
        "Sylph.top_species",
        "Sylph.top_abundance_percent",
        "Sylph.top_sequence_abundance_percent",
        "Sylph.top_adjusted_ani",
        "Sylph.number_of_genomes",
        "Sylph.species_name",
        "Sylph.taxonomic_abundances_percent",
        "Sylph.sequence_abundances_percent",
        "Quast.qc_status",
        "Quast.# contigs (>= 0 bp).status",
        "Quast.# contigs (>= 0 bp)",
        "Quast.N50.status",
        "Quast.N50",
        "Quast.Total length (>= 0 bp).status",
        "Quast.Total length (>= 0 bp)",
        "Quast.GC (%).status",
        "Quast.GC (%)",
        "Quast.Largest contig",
        "Checkm.qc_status",
        "Checkm.Completeness.status",
        "Checkm.Completeness",
        "Checkm.Contamination.status",
        "Checkm.Contamination",
        "Checkm.GC_Content",
        "Checkm.Genome_Size",
        "Checkm.Contig_N50",
        "Checkm.Total_Contigs",
        "Checkm.Total_Coding_Sequences",
        "Fastp.qc_status",
        "Fastp.after_filtering_q30_rate.status",
        "Fastp.after_filtering_q30_rate",
        "Fastp.passed_filter_rate",
        "Fastp.duplication_rate",
        "Busco.qc_status",
        "Busco.Complete.status",
        "Busco.Complete",
        "Busco.Missing.status",
        "Busco.Missing",
        "Busco.Duplicated",
        "Busco.Fragmented",
        "Busco.Lineage",
        "Ariba.qc_status",
        "Ariba.percent.status",
        "Ariba.percent",
        "Ariba.passed",
        "Ariba.total",
        "Ariba.not_called",
        "Sylph.genomes",
        "report_schema_version",
        "qualibact_tier",
    ]

    with open(concise_path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    assert lines[0] == ",".join(expected_concise_columns), "Concise header order mismatch"
    row = dict(zip(expected_concise_columns, lines[1].split(","), strict=True))
    assert row["Ariba.qc_status"] == "PASS"
    assert row["Ariba.percent"] == "100.0"

    # Basic sanity checks for detailed file: contains representative keys
    with open(detailed_path, encoding="utf-8") as f_det:
        detailed_content = f_det.read()
    assert "Speciator.speciesName" in detailed_content
    assert "Quast.N50" in detailed_content
    assert "Checkm.Completeness" in detailed_content
