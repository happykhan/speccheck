from click import unstyle
from typer.testing import CliRunner

from speccheck.cli import app


def test_global_verbose_and_quiet_are_mutually_exclusive():
    result = CliRunner().invoke(app, ["--verbose", "--quiet", "modules"])

    assert result.exit_code != 0
    assert "verbose and" in unstyle(result.output)


def test_version_callback_prints_version():
    result = CliRunner().invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "speccheck version:" in result.output


def test_collect_command_dispatches_options(monkeypatch, tmp_path):
    calls = {}

    def fake_collect(
        organism,
        filepaths,
        criteria_file,
        output_file,
        sample,
        metadata,
        *,
        allow_unknown_organism,
        assembly_type,
        fail_on_not_evaluated,
    ):
        calls.update(
            {
                "organism": organism,
                "filepaths": filepaths,
                "criteria_file": criteria_file,
                "output_file": output_file,
                "sample": sample,
                "metadata": metadata,
                "allow_unknown_organism": allow_unknown_organism,
                "assembly_type": assembly_type,
                "fail_on_not_evaluated": fail_on_not_evaluated,
            }
        )

    monkeypatch.setattr("speccheck.cli.collect_func", fake_collect)

    input_dir = tmp_path / "inputs"
    input_dir.mkdir()
    criteria_file = tmp_path / "criteria.csv"
    metadata = tmp_path / "metadata.csv"
    output_file = tmp_path / "collect.csv"

    result = CliRunner().invoke(
        app,
        [
            "collect",
            str(input_dir),
            "--organism",
            "Escherichia coli",
            "--sample",
            "SAMPLE_001",
            "--criteria-file",
            str(criteria_file),
            "--output-file",
            str(output_file),
            "--metadata",
            str(metadata),
            "--assembly-type",
            "hybrid",
            "--allow-unknown-organism",
            "--fail-on-not-evaluated",
        ],
    )

    assert result.exit_code == 0
    assert calls["organism"] == "Escherichia coli"
    assert calls["filepaths"] == [str(input_dir)]
    assert calls["criteria_file"] == str(criteria_file)
    assert calls["output_file"] == str(output_file)
    assert calls["sample"] == "SAMPLE_001"
    assert calls["metadata"] == str(metadata)
    assert calls["allow_unknown_organism"] is True
    assert calls["assembly_type"] == "hybrid"
    assert calls["fail_on_not_evaluated"] is True


def test_summary_command_dispatches_reporting_options(monkeypatch, tmp_path):
    calls = {}

    def fake_summary(
        directory,
        output,
        species,
        sample,
        templates,
        plot,
        *,
        xlsx_output,
        interactive_tables,
        qualifyr_style,
        qualibact_compat,
        qualibact_warn_as_fail,
    ):
        calls.update(
            {
                "directory": directory,
                "output": output,
                "species": species,
                "sample": sample,
                "templates": templates,
                "plot": plot,
                "xlsx_output": xlsx_output,
                "interactive_tables": interactive_tables,
                "qualifyr_style": qualifyr_style,
                "qualibact_compat": qualibact_compat,
                "qualibact_warn_as_fail": qualibact_warn_as_fail,
            }
        )

    monkeypatch.setattr("speccheck.cli.summary_func", fake_summary)

    collect_dir = tmp_path / "collect"
    collect_dir.mkdir()
    output_dir = tmp_path / "report"
    template = tmp_path / "report.html"
    xlsx = tmp_path / "report.xlsx"

    result = CliRunner().invoke(
        app,
        [
            "summary",
            str(collect_dir),
            "--output",
            str(output_dir),
            "--species",
            "species",
            "--sample",
            "sample",
            "--templates",
            str(template),
            "--plot",
            "--xlsx-output",
            str(xlsx),
            "--no-interactive-tables",
            "--qualifyr-style",
            "--qualibact-compat",
            "--qualibact-warn-as-fail",
        ],
    )

    assert result.exit_code == 0
    assert calls["directory"] == str(collect_dir)
    assert calls["output"] == str(output_dir)
    assert calls["species"] == "species"
    assert calls["sample"] == "sample"
    assert calls["templates"] == str(template)
    assert calls["plot"] is True
    assert calls["xlsx_output"] == str(xlsx)
    assert calls["interactive_tables"] is False
    assert calls["qualifyr_style"] is True
    assert calls["qualibact_compat"] is True
    assert calls["qualibact_warn_as_fail"] is True


def test_check_command_dispatches_update_options(monkeypatch, tmp_path):
    calls = {}

    def fake_check(criteria_file, update=False, update_url=None):
        calls.update(
            {
                "criteria_file": criteria_file,
                "update": update,
                "update_url": update_url,
            }
        )

    monkeypatch.setattr("speccheck.cli.check_func", fake_check)

    criteria_file = tmp_path / "criteria.csv"
    result = CliRunner().invoke(
        app,
        [
            "check",
            "--criteria-file",
            str(criteria_file),
            "--update",
            "--update-url",
            "https://example.invalid/thresholds.csv",
        ],
    )

    assert result.exit_code == 0
    assert calls == {
        "criteria_file": str(criteria_file),
        "update": True,
        "update_url": "https://example.invalid/thresholds.csv",
    }


def test_collect_pipeline_accepts_ghru_layout(monkeypatch, tmp_path):
    calls = {}

    def fake_collect_pipeline_outputs(
        output_tree,
        output_dir,
        criteria_file,
        *,
        organism,
        metadata,
        allow_unknown_organism,
        fail_on_not_evaluated,
        work_dir,
        sample,
        verbose=False,
    ):
        calls.update(
            {
                "output_tree": output_tree,
                "output_dir": output_dir,
                "criteria_file": criteria_file,
                "organism": organism,
                "metadata": metadata,
                "allow_unknown_organism": allow_unknown_organism,
                "fail_on_not_evaluated": fail_on_not_evaluated,
                "work_dir": work_dir,
                "sample": sample,
                "verbose": verbose,
            }
        )

    monkeypatch.setattr("speccheck.cli._collect_pipeline_outputs", fake_collect_pipeline_outputs)

    output_tree = tmp_path / "results"
    collect_dir = tmp_path / "collect"
    output_tree.mkdir()

    result = CliRunner().invoke(
        app,
        [
            "collect-pipeline",
            str(output_tree),
            str(collect_dir),
            "--layout",
            "ghru",
            "--sample",
            "SAMPLE_001",
            "--organism",
            "Escherichia coli",
        ],
    )

    assert result.exit_code == 0
    assert calls["output_tree"] == str(output_tree)
    assert calls["output_dir"] == str(collect_dir)
    assert calls["organism"] == "Escherichia coli"
    assert calls["sample"] == ["SAMPLE_001"]


def test_collect_ghru_remains_available_as_compatibility_alias():
    result = CliRunner().invoke(app, ["collect-ghru", "--help"])

    assert result.exit_code == 0
    assert "Compatibility alias" in result.output
    assert "GHRU" in result.output
    assert "Assembly layout" in result.output


def test_collect_pipeline_rejects_unknown_layout(tmp_path):
    output_tree = tmp_path / "results"
    collect_dir = tmp_path / "collect"
    output_tree.mkdir()

    result = CliRunner().invoke(
        app,
        [
            "collect-pipeline",
            str(output_tree),
            str(collect_dir),
            "--layout",
            "unknown",
        ],
    )

    assert result.exit_code != 0
    assert "Only --layout ghru is currently supported" in unstyle(result.output)


def test_modules_command_lists_builtin_parsers():
    result = CliRunner().invoke(app, ["modules"])

    assert result.exit_code == 0
    assert "Speciator" in result.output
    assert "Fastp" in result.output


def test_inspect_command_reports_recognised_and_unrecognised_files(tmp_path):
    unknown_file = tmp_path / "unknown.txt"
    unknown_file.write_text("not a recognised QC file\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "inspect",
            "tests/collect_test_data/test_sample1.short.tsv",
            str(unknown_file),
        ],
    )

    assert result.exit_code == 0
    assert "Speciator" in result.output
    assert "not recognised" in result.output
