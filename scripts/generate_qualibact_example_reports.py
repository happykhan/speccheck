#!/usr/bin/env python3
"""Generate manuscript-friendly example reports from pinned QualiBact fixtures."""

import pandas as pd
from pathlib import Path

from speccheck.main import summary
from speccheck.report import get_default_template_path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "qualibact"
OUTPUT_ROOT = REPO_ROOT / "examples" / "qualibact_ecoli"


def build_speccheck_summary_input(source_csv, destination):
    source = pd.read_csv(source_csv)
    records = []
    for _, row in source.iterrows():
        qc_pass = str(row["qc_verdict"]).lower() == "pass"
        n50_pass = str(row["N50_verdict"]).lower() == "pass"
        contig_pass = str(row["no_of_contigs_verdict"]).lower() == "pass"
        genome_pass = str(row["Genome_Size_verdict"]).lower() == "pass"
        checkm_pass = qc_pass and float(row["Contamination"]) <= 2.0
        records.append(
            {
                "sample_id": row["sample"],
                "all_checks_passed": qc_pass,
                "Checkm.all_checks_passed": checkm_pass,
                "Checkm.Completeness": row["Completeness_Specific"],
                "Checkm.Contamination": row["Contamination"],
                "Checkm.GC": row["GC_Content"],
                "Checkm.Genome size (bp)": row["Genome_Size"],
                "Checkm.# contigs": row["number"],
                "Checkm.N50 (scaffolds)": row["N50"],
                "Checkm.Completeness.check": True,
                "Checkm.Contamination.check": float(row["Contamination"]) <= 2.0,
                "Quast.all_checks_passed": n50_pass and contig_pass and genome_pass,
                "Quast.N50": row["N50"],
                "Quast.N50.check": n50_pass,
                "Quast.# contigs (>= 0 bp)": row["number"],
                "Quast.# contigs (>= 0 bp).check": contig_pass,
                "Quast.Total length (>= 0 bp)": row["Genome_Size"],
                "Quast.Total length": row["Genome_Size"],
                "Quast.Total length (>= 0 bp).check": genome_pass,
                "Quast.GC (%)": row["GC_Content"],
                "Quast.GC (%).check": str(row["GC_Content_verdict"]).lower() == "pass",
                "Quast.Largest contig": row["longest"],
                "Speciator.all_checks_passed": True,
                "Speciator.speciesName": row["species_sylph"],
                "Speciator.confidence": "good",
                "Sylph.all_checks_passed": True,
                "Sylph.top_species": row["species_sylph"],
                "Sylph.top_taxonomic_abundance": 0.95 if qc_pass else 0.75,
                "Sylph.number_of_genomes": 1,
            }
        )
    pd.DataFrame(records).to_csv(destination, index=False)


def generate_report(name, fixture_name):
    input_dir = OUTPUT_ROOT / name / "input"
    output_dir = OUTPUT_ROOT / name / "report"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_csv = input_dir / f"{name}.csv"
    build_speccheck_summary_input(FIXTURE_DIR / fixture_name, input_csv)

    summary(
        str(input_dir),
        str(output_dir),
        "Speciator.speciesName",
        "sample_id",
        get_default_template_path(),
        plot=True,
        xlsx_output=str(output_dir / "report.xlsx"),
        interactive_tables=True,
        qualifyr_style=True,
    )


def main():
    generate_report("pass_only", "ecoli_pass_subset.csv")
    generate_report("fail_only", "ecoli_fail_subset.csv")


if __name__ == "__main__":
    main()
