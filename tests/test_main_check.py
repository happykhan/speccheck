import logging

from speccheck.main import check


def test_check_reports_missing_criteria_file(caplog, tmp_path):
    caplog.set_level(logging.ERROR)

    check(str(tmp_path / "missing.csv"))

    assert "Criteria file not found" in caplog.text


def test_check_reports_invalid_extension_and_missing_baseline(caplog, tmp_path):
    criteria_file = tmp_path / "criteria.txt"
    criteria_file.write_text(
        "\n".join(
            [
                "species,assembly_type,software,field,operator,value,special_field",
                "Escherichia coli,short,Quast,N50,>=,10000,",
            ]
        ),
        encoding="utf-8",
    )
    caplog.set_level(logging.ERROR)

    check(str(criteria_file))

    assert "Criteria file is not a valid csv file." in caplog.text
    assert "No criteria found for species 'all'." in caplog.text


def test_check_reports_missing_required_columns(caplog, tmp_path):
    criteria_file = tmp_path / "criteria.csv"
    criteria_file.write_text("species,software,field\nall,Quast,N50\n", encoding="utf-8")
    caplog.set_level(logging.ERROR)

    check(str(criteria_file))

    assert "Missing required column: assembly_type" in caplog.text
    assert "Missing required column: operator" in caplog.text


def test_check_logs_valid_criteria(caplog, tmp_path):
    criteria_file = tmp_path / "criteria.csv"
    criteria_file.write_text(
        "\n".join(
            [
                "species,assembly_type,software,field,operator,value,special_field",
                "all,all,Quast,N50,>=,10000,",
            ]
        ),
        encoding="utf-8",
    )
    caplog.set_level(logging.INFO)

    check(str(criteria_file))

    assert "Criteria file is valid." in caplog.text


def test_check_can_update_before_validating(monkeypatch, tmp_path):
    calls = {}
    criteria_file = tmp_path / "criteria.csv"
    criteria_file.write_text(
        "\n".join(
            [
                "species,assembly_type,software,field,operator,value,special_field",
                "all,all,Quast,N50,>=,10000,",
            ]
        ),
        encoding="utf-8",
    )

    def fake_update(path, url):
        calls["path"] = path
        calls["url"] = url
        return True

    monkeypatch.setattr("speccheck.main.update_criteria_file", fake_update)

    check(str(criteria_file), update=True, update_url="https://example.invalid/thresholds.csv")

    assert calls == {
        "path": str(criteria_file),
        "url": "https://example.invalid/thresholds.csv",
    }
