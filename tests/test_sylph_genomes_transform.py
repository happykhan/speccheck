from speccheck.collect import write_to_file


def test_sylph_genomes_accession_extraction(tmp_path):
    # Provided example paths should reduce to just accessions
    raw = (
        "gtdb_genomes_reps_r220/database/GCF/000/742/135/GCF_000742135.1_genomic.fna.gz;"
        "gtdb_genomes_reps_r220/database/GCF/003/697/165/GCF_003697165.2_genomic.fna.gz"
    )
    out = tmp_path / "result.csv"

    qc_report = {
        "sample_id": "S1",
        "all_checks_passed": True,
        "Speciator.all_checks_passed": True,
        "Speciator.speciesName": "Escherichia coli",
        "Depth.all_checks_passed": True,
        "Depth.Depth": 30,
        "Depth.Read_type": "short",
        "Sylph.all_checks_passed": True,
        "Sylph.top_species": "Escherichia coli",
        "Sylph.top_taxonomic_abundance": 0.9,
        "Sylph.genomes": raw,
        "Quast.all_checks_passed": True,
        "Quast.# contigs (>= 0 bp).check": True,
        "Quast.# contigs": 10,
        "Quast.N50.check": True,
        "Quast.N50": 1000,
        "Quast.Total length (>= 0 bp).check": True,
        "Quast.Total length": 5000,
        "Quast.GC (%).check": True,
        "Quast.GC (%)": 50.0,
        "Quast.Largest contig": 2000,
        "Checkm.all_checks_passed": True,
        "Checkm.Completeness.check": True,
        "Checkm.Completeness": 99.0,
        "Checkm.Contamination.check": True,
        "Checkm.Contamination": 0.5,
    }

    write_to_file(out, qc_report)

    concise = out.read_text(encoding="utf-8").splitlines()
    concise_header = concise[0].split(",")
    concise_row = concise[1].split(",")

    sylph_idx = concise_header.index("Sylph.genomes")
    assert concise_row[sylph_idx] == "GCF_000742135.1;GCF_003697165.2"

    # Detailed file should also have the sanitized value
    detailed = (out.parent / f"detailed.{out.name}").read_text(encoding="utf-8").splitlines()
    det_header = detailed[0].split(",")
    det_row = detailed[1].split(",")
    det_idx = det_header.index("Sylph.genomes")
    assert det_row[det_idx] == "GCF_000742135.1;GCF_003697165.2"
