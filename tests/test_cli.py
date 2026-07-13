from typer.testing import CliRunner

from speccheck.cli import app


def test_collect_pipeline_help_documents_layout():
    result = CliRunner().invoke(app, ["collect-pipeline", "--help"])

    assert result.exit_code == 0
    assert "collect-pipeline" in result.output
    assert "--layout" in result.output
    assert "ghru" in result.output


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
    assert "Only --layout ghru is currently supported" in result.output
