import csv
import os

import pytest

from speccheck.main import collect, summary
from speccheck.report import get_default_template_path


def test_collect():

    # Define the input filepaths
    input_filepaths = [
        "tests/collect_test_data/report.tsv",
        "tests/collect_test_data/checkm.short.tsv",
        "tests/collect_test_data/sylph.tsv",
        "tests/collect_test_data/test_sample1.short.tsv",
        "tests/collect_test_data/ariba_mlst_report.details.tsv",
    ]
    criteria_file = "criteria.csv"
    output_file = "collect_output.csv"

    sample_id = "Sample1"
    # Run the collect function
    collect("Mycoplasma genitalium", input_filepaths, criteria_file, output_file, sample_id)

    # Check if the output file is created
    assert os.path.isfile(output_file)

    # Check the content of the output file
    with open(output_file, encoding="utf-8") as f:
        content = f.read()
        assert "Sample1" in content
        assert "Quast.N50.check" in content
    os.remove(output_file)
    os.remove(f"detailed.{output_file}")


def test_collect_rejects_unknown_organism_by_default(tmp_path):
    output_file = tmp_path / "collect_output.csv"

    with pytest.raises(ValueError, match="Organism name was not provided"):
        collect(
            None,
            ["tests/collect_test_data/report.tsv"],
            "criteria.csv",
            str(output_file),
            "Sample1",
        )


def test_collect_output_can_generate_plotted_summary(tmp_path):
    collect_dir = tmp_path / "collect"
    summary_dir = tmp_path / "summary"
    collect_dir.mkdir()
    depth_file = tmp_path / "depth.tsv"
    depth_file.write_text(
        "Sample_id\tRead_type\tDepth\nE2E_SAMPLE\tshort\t42.5\n", encoding="utf-8"
    )

    collect(
        "Mycoplasma genitalium",
        [
            "tests/collect_test_data/report.tsv",
            "tests/collect_test_data/checkm.short.tsv",
            "tests/collect_test_data/sylph.tsv",
            "tests/collect_test_data/test_sample1.short.tsv",
            "tests/collect_test_data/ariba_mlst_report.details.tsv",
            str(depth_file),
        ],
        "criteria.csv",
        str(collect_dir / "E2E_SAMPLE.csv"),
        "E2E_SAMPLE",
    )

    summary(
        str(collect_dir),
        str(summary_dir),
        "Speciator.speciesName",
        "sample_id",
        get_default_template_path(),
        plot=True,
        xlsx_output=str(summary_dir / "report.xlsx"),
        qualifyr_style=True,
    )

    assert (summary_dir / "report.csv").exists()
    assert (summary_dir / "report.html").exists()
    assert (summary_dir / "report.xlsx").exists()
    with open(collect_dir / "E2E_SAMPLE.csv", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["speccheck_assembly_type"] == "short"
    assert rows[0]["speccheck_fail_on_not_evaluated"] == "False"
    assert rows[0]["speccheck_version"]
    assert len(rows[0]["speccheck_criteria_sha256"]) == 64
    assert rows[0]["speccheck_input_file_count"] == "6"
    report_html = (summary_dir / "report.html").read_text(encoding="utf-8")
    assert "Speciator" in report_html
    assert "Confidence" in report_html


def test_collect_filters_criteria_by_assembly_type(tmp_path):
    criteria_file = tmp_path / "criteria.csv"
    criteria_file.write_text(
        "\n".join(
            [
                "species,assembly_type,software,field,operator,value,special_field",
                "Mycoplasma genitalium,all,Quast,GC (%),>=,0,",
                "Mycoplasma genitalium,short,Quast,N50,>=,999999,",
                "Mycoplasma genitalium,long,Quast,N50,>=,0,",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    output_file = tmp_path / "long.csv"

    collect(
        "Mycoplasma genitalium",
        ["tests/collect_test_data/report.tsv"],
        str(criteria_file),
        str(output_file),
        "LONG_SAMPLE",
        assembly_type="long",
    )

    with open(output_file, encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["Quast.N50.check"] == "PASSED"
    assert row["speccheck_assembly_type"] == "long"


def test_collect_reports_not_evaluated_missing_metrics(tmp_path):
    criteria_file = tmp_path / "criteria.csv"
    criteria_file.write_text(
        "\n".join(
            [
                "species,assembly_type,software,field,operator,value,special_field",
                "Mycoplasma genitalium,all,Quast,Missing manuscript metric,>=,1,",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    output_file = tmp_path / "missing.csv"

    collect(
        "Mycoplasma genitalium",
        ["tests/collect_test_data/report.tsv"],
        str(criteria_file),
        str(output_file),
        "MISSING_SAMPLE",
    )

    with open(output_file, encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["Quast.Missing manuscript metric.check"] == "NOT_EVALUATED"
    assert row["Quast.all_checks_passed"] == "PASSED"
    assert row["all_checks_passed"] == "PASSED"
    assert row["speccheck_not_evaluated_count"] == "1"


def test_collect_can_fail_on_not_evaluated_missing_metrics(tmp_path):
    criteria_file = tmp_path / "criteria.csv"
    criteria_file.write_text(
        "\n".join(
            [
                "species,assembly_type,software,field,operator,value,special_field",
                "Mycoplasma genitalium,all,Quast,Missing manuscript metric,>=,1,",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    output_file = tmp_path / "missing_strict.csv"

    collect(
        "Mycoplasma genitalium",
        ["tests/collect_test_data/report.tsv"],
        str(criteria_file),
        str(output_file),
        "STRICT_MISSING_SAMPLE",
        fail_on_not_evaluated=True,
    )

    with open(output_file, encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["Quast.Missing manuscript metric.check"] == "NOT_EVALUATED"
    assert row["Quast.all_checks_passed"] == "FAILED"
    assert row["all_checks_passed"] == "FAILED"
