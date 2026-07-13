import csv

import pytest

from speccheck.criteria import get_criteria_layers, validate_criteria


HEADERS = [
    "species",
    "assembly_type",
    "software",
    "field",
    "operator",
    "value",
    "severity",
    "source",
    "special_field",
]


def _write_criteria(path, rows, headers=HEADERS):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def _valid_row(**overrides):
    row = {
        "species": "all",
        "assembly_type": "all",
        "software": "Quast",
        "field": "N50",
        "operator": ">=",
        "value": "10000",
        "severity": "fail",
        "source": "test",
        "special_field": "",
    }
    row.update(overrides)
    return row


def test_validate_criteria_reports_missing_file(tmp_path):
    errors, warnings = validate_criteria(tmp_path / "missing.csv")

    assert errors == [f"File not found: {tmp_path / 'missing.csv'}"]
    assert warnings == []


def test_validate_criteria_rejects_invalid_csv(tmp_path):
    criteria_file = tmp_path / "criteria.csv"
    criteria_file.write_text("not,csv\n'unterminated\n", encoding="utf-8")

    errors, warnings = validate_criteria(criteria_file)

    assert any("not a valid CSV" in error for error in errors)
    assert warnings == []


def test_validate_criteria_reports_missing_and_unexpected_headers(tmp_path):
    criteria_file = tmp_path / "criteria.csv"
    _write_criteria(
        criteria_file,
        [{"species": "all", "software": "Quast", "field": "N50", "extra": "value"}],
        headers=["species", "software", "field", "extra"],
    )

    errors, warnings = validate_criteria(criteria_file)

    assert len(errors) == 1
    assert "Invalid headers" in errors[0]
    assert "assembly_type" in errors[0]
    assert "extra" in errors[0]
    assert warnings == []


def test_validate_criteria_reports_row_level_errors_and_warnings(tmp_path):
    criteria_file = tmp_path / "criteria.csv"
    _write_criteria(
        criteria_file,
        [
            _valid_row(software="UnknownTool"),
            _valid_row(operator="between"),
            _valid_row(operator="regex", value="["),
            _valid_row(value="not numeric"),
            _valid_row(severity="critical"),
            _valid_row(special_field="organism"),
            _valid_row(species="", field=""),
        ],
    )

    errors, warnings = validate_criteria(criteria_file)

    assert any("Invalid operator 'between'" in error for error in errors)
    assert any("Invalid regex pattern" in error for error in errors)
    assert any("must be numeric" in error for error in errors)
    assert any("Invalid severity" in error for error in errors)
    assert any("Missing required fields" in error for error in errors)
    assert any("Unsupported software 'UnknownTool'" in warning for warning in warnings)
    assert any("'special_field' value is not supported" in warning for warning in warnings)


def test_get_criteria_layers_applies_species_specific_overrides(tmp_path):
    criteria_file = tmp_path / "criteria.csv"
    _write_criteria(
        criteria_file,
        [
            _valid_row(field="N50", value="10000"),
            _valid_row(field="GC", value="55"),
            _valid_row(species="Escherichia coli", field="N50", value="20000"),
        ],
    )

    layers = get_criteria_layers(criteria_file, species="Escherichia coli")

    assert layers["baseline_overridden_count"] == 1
    assert [row["field"] for row in layers["baseline"]] == ["GC"]
    assert layers["species"][0]["field"] == "N50"
    assert layers["species"][0]["value"] == 20000


def test_get_criteria_layers_without_species_keeps_baseline(tmp_path):
    criteria_file = tmp_path / "criteria.csv"
    _write_criteria(
        criteria_file,
        [
            _valid_row(field="N50", value="10000"),
            _valid_row(species="Escherichia coli", field="N50", value="20000"),
        ],
    )

    layers = get_criteria_layers(criteria_file)

    assert layers["baseline_overridden_count"] == 0
    assert [row["field"] for row in layers["baseline"]] == ["N50"]
    assert layers["species"] == []
