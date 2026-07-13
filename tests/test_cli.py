from click import unstyle
from typer.testing import CliRunner

from speccheck.cli import app


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
