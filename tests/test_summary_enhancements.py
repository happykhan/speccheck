import openpyxl
import pandas as pd
from pathlib import Path

from speccheck.main import summary
from speccheck.report import get_default_template_path


def _build_speccheck_summary_input(source_csv, destination):
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


def test_summary_generates_interactive_html_and_xlsx(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    _build_speccheck_summary_input("tests/qualibact/ecoli_pass_subset.csv", input_dir / "pass.csv")
    _build_speccheck_summary_input("tests/qualibact/ecoli_fail_subset.csv", input_dir / "fail.csv")

    xlsx_output = output_dir / "report.xlsx"
    summary(
        str(input_dir),
        str(output_dir),
        "Speciator.speciesName",
        "sample_id",
        get_default_template_path(),
        plot=True,
        xlsx_output=str(xlsx_output),
        qualifyr_style=True,
    )

    report_html = (output_dir / "report.html").read_text(encoding="utf-8")
    assert (output_dir / "report.csv").exists()
    assert (output_dir / "report.html").exists()
    assert not (output_dir / "bulma.css").exists()
    assert xlsx_output.exists()
    assert "table-filter" in report_html
    assert "qualifyr-like layout" in report_html
    assert "Speciator" in report_html
    assert "Confidence" in report_html
    assert '<link rel="stylesheet" href="bulma.css">' not in report_html
    assert ".report-header" in report_html

    workbook = openpyxl.load_workbook(xlsx_output)
    assert "report" in workbook.sheetnames
    assert "qc_status" in workbook.sheetnames


def test_summary_respects_no_interactive_tables(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    _build_speccheck_summary_input("tests/qualibact/ecoli_pass_subset.csv", input_dir / "pass.csv")

    summary(
        str(input_dir),
        str(output_dir),
        "Speciator.speciesName",
        "sample_id",
        get_default_template_path(),
        plot=True,
        interactive_tables=False,
        qualifyr_style=True,
    )

    report_html = (output_dir / "report.html").read_text(encoding="utf-8")
    assert 'class="table-filter"' not in report_html
    assert 'class="table report-table js-sort-filter"' not in report_html
    assert "parseValue" not in report_html
    assert '<link rel="stylesheet" href="bulma.css">' not in report_html
