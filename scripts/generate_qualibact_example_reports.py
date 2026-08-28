#!/usr/bin/env python3
"""Generate worked-example reports from pinned QualiBact fixtures."""

from pathlib import Path

import pandas as pd

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
                "speccheck_qc": "PASS" if qc_pass else "FAIL",
                "Checkm.qc_status": "PASS" if checkm_pass else "FAIL",
                "Checkm.Completeness": row["Completeness_Specific"],
                "Checkm.Contamination": row["Contamination"],
                "Checkm.GC_Content": row["GC_Content"],
                "Checkm.Genome_Size": row["Genome_Size"],
                "Checkm.Total_Contigs": row["number"],
                "Checkm.Contig_N50": row["N50"],
                "Checkm.Total_Coding_Sequences": row["Total_Coding_Sequences"],
                "Checkm.Completeness.status": "PASS",
                "Checkm.Contamination.status": (
                    "PASS" if float(row["Contamination"]) <= 2.0 else "FAIL"
                ),
                "Quast.qc_status": ("PASS" if n50_pass and contig_pass and genome_pass else "FAIL"),
                "Quast.N50": row["N50"],
                "Quast.N50.status": "PASS" if n50_pass else "FAIL",
                "Quast.# contigs (>= 0 bp)": row["number"],
                "Quast.# contigs (>= 0 bp).status": "PASS" if contig_pass else "FAIL",
                "Quast.Total length (>= 0 bp)": row["Genome_Size"],
                "Quast.Total length (>= 0 bp).status": "PASS" if genome_pass else "FAIL",
                "Quast.GC (%)": row["GC_Content"],
                "Quast.GC (%).status": (
                    "PASS" if str(row["GC_Content_verdict"]).lower() == "pass" else "FAIL"
                ),
                "Quast.Largest contig": row["longest"],
                "Speciator.qc_status": "PASS",
                "Speciator.speciesName": row["species_sylph"],
                "Speciator.confidence": "good",
                "Sylph.qc_status": "PASS",
                "Sylph.top_species": row["species_sylph"],
                "Sylph.top_abundance_percent": 95.0 if qc_pass else 75.0,
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
        qualibact_compat=True,
    )


def main():
    generate_report("pass_only", "ecoli_pass_subset.csv")
    generate_report("fail_only", "ecoli_fail_subset.csv")


if __name__ == "__main__":
    main()
