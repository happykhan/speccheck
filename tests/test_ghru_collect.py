import csv
import shutil

from speccheck.config import get_default_criteria_path
from speccheck.ghru import discover_ghru_sample_files
from speccheck.main import collect_ghru


def _write_depth_report(path, sample_id="test_sample1", read_type="short", depth="42.0"):
    path.write_text(
        f"Sample_id\tRead_type\tDepth\n{sample_id}\t{read_type}\t{depth}\n",
        encoding="utf-8",
    )


def _stage_ghru_fixture(tmp_path):
    output_dir = tmp_path / "ghru_output"
    (output_dir / "quast_summary").mkdir(parents=True)
    (output_dir / "checkm_summary").mkdir()
    (output_dir / "speciation_summary").mkdir()
    (output_dir / "sylph_summary").mkdir()

    shutil.copyfile(
        "tests/collect_test_data/report.tsv",
        output_dir / "quast_summary" / "ori_test_sample1.short.report.tsv",
    )
    shutil.copyfile(
        "tests/collect_test_data/checkm.short.tsv",
        output_dir / "checkm_summary" / "test_sample1.short.tsv",
    )
    shutil.copyfile(
        "tests/collect_test_data/test_sample1.short.tsv",
        output_dir / "speciation_summary" / "test_sample1.short.tsv",
    )
    shutil.copyfile(
        "tests/collect_test_data/sylph.tsv",
        output_dir / "sylph_summary" / "test_sample1_slyph_report.tsv",
    )

    return output_dir


def test_discover_ghru_sample_files_finds_standard_outputs(tmp_path):
    output_dir = _stage_ghru_fixture(tmp_path)
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    _write_depth_report(work_dir / "test_sample1.shortshort_reads.depth.tsv")

    sample_map = discover_ghru_sample_files(str(output_dir), work_dir=str(work_dir))

    assert sorted(sample_map) == ["test_sample1"]
    sample = sample_map["test_sample1"]
    assert sample.assembly_type == "short"
    assert len(sample.files) == 5
    assert any(path.endswith("ori_test_sample1.short.report.tsv") for path in sample.files)
    assert any(path.endswith("test_sample1.short.tsv") for path in sample.files)
    assert any(path.endswith("test_sample1_slyph_report.tsv") for path in sample.files)
    assert any(path.endswith(".depth.tsv") for path in sample.files)


def test_collect_ghru_writes_per_sample_csv(tmp_path):
    output_dir = _stage_ghru_fixture(tmp_path)
    collect_dir = tmp_path / "collect"

    written = collect_ghru(
        str(output_dir),
        str(collect_dir),
        get_default_criteria_path(),
        organism="Mycoplasma genitalium",
    )

    assert written == [str(collect_dir / "test_sample1.csv")]

    with open(collect_dir / "test_sample1.csv", encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))

    assert row["sample_id"] == "test_sample1"
    assert row["Speciator.speciesName"] == "Mycoplasma genitalium"
    assert row["Checkm.Completeness"] == "93.2"
    assert row["Quast.N50"] == "579729"
