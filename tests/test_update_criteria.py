import csv
import json
from pathlib import Path

from speccheck.update_criteria import (
    QUALIBACT_DEFAULT_URL,
    QUALIBACT_INDEX_URL,
    qualibact_rows_to_criteria_rows,
    update_criteria_file,
)


def test_qualibact_rows_to_criteria_rows_maps_thresholds():
    with open("tests/qualibact/thresholds_subset.csv", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows.append(
        {
            "species": "Escherichia coli",
            "scheme": "qualibact-v1.0",
            "metric": "Total_Coding_Sequences",
            "FINAL_lower": "",
            "FINAL_upper": "6500",
            "WARN_lower": "",
            "WARN_upper": "5800",
            "source": "external",
        }
    )
    rows.append(
        {
            "species": "Escherichia coli",
            "scheme": "enterobase-v2.3",
            "metric": "Completeness",
            "FINAL_lower": "99",
            "FINAL_upper": "",
            "WARN_lower": "",
            "WARN_upper": "",
            "source": "external",
        }
    )

    criteria_rows = qualibact_rows_to_criteria_rows(rows)

    assert any(
        row["software"] == "Checkm"
        and row["field"] == "Genome size (bp)"
        and row["operator"] == ">="
        and row["value"] == 3700000
        for row in criteria_rows
    )
    assert any(
        row["software"] == "Quast"
        and row["field"] == "N50"
        and row["operator"] == ">="
        and row["value"] == 13000
        for row in criteria_rows
    )
    assert any(
        row["software"] == "Speciator"
        and row["field"] == "speciesName"
        and row["special_field"] == "species_field"
        for row in criteria_rows
    )
    assert any(
        row["software"] == "Checkm"
        and row["field"] == "Total_Coding_Sequences"
        and row["operator"] == "<="
        and row["value"] == 6500
        for row in criteria_rows
    )
    assert not any(
        row["software"] == "Checkm" and row["field"] == "Marker lineage" for row in criteria_rows
    )


def test_preferred_scheme_from_index_is_used_even_when_not_qualibact_v1():
    rows = [
        {
            "species": "Example_species",
            "scheme": scheme,
            "metric": "Genome_Size",
            "FINAL_lower": lower,
            "FINAL_upper": "",
            "WARN_lower": "",
            "WARN_upper": "",
            "source": "test",
        }
        for scheme, lower in [("qualibact-v1.0", "100"), ("REFSEQ-QC-v1", "200")]
    ]
    criteria = qualibact_rows_to_criteria_rows(rows, {"Example_species": "REFSEQ-QC-v1"})
    genome_lower = [
        row
        for row in criteria
        if row["species"] == "Example species"
        and row["software"] == "Checkm"
        and row["field"] == "Genome size (bp)"
    ]
    assert genome_lower[0]["value"] == 200
    assert genome_lower[0]["source"] == "REFSEQ-QC-v1"


def test_update_criteria_file_preserves_unmanaged_rows(tmp_path, monkeypatch):
    criteria_file = tmp_path / "criteria.csv"
    criteria_file.write_text(
        "\n".join(
            [
                "species,assembly_type,software,field,operator,value,special_field",
                "Escherichia coli,short,Ariba,percent,=,100,",
            ]
        ),
        encoding="utf-8",
    )

    fixture_text = Path("tests/qualibact/thresholds_subset.csv").read_text(encoding="utf-8")

    class MockResponse:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        "speccheck.update_criteria.requests.get",
        lambda *_args, **_kwargs: MockResponse(fixture_text),
    )

    snapshot_dir = tmp_path / "snapshot"
    update_criteria_file(
        criteria_file,
        "https://example.invalid/thresholds.csv",
        snapshot_dir=snapshot_dir,
    )

    written_rows = list(csv.DictReader(criteria_file.open(encoding="utf-8")))
    assert any(
        row["software"] == "Ariba" and row["field"] == "percent" and row["value"] == "100"
        for row in written_rows
    )
    assert any(
        row["software"] == "Checkm"
        and row["field"] == "Genome size (bp)"
        and row["operator"] == ">="
        and row["value"] == "3700000"
        for row in written_rows
    )
    assert not any(
        row["software"] == "Checkm" and row["field"] == "Marker lineage" for row in written_rows
    )
    assert (snapshot_dir / "qualibact_snapshot.csv").exists()
    assert (snapshot_dir / "qualibact_snapshot_metadata.csv").exists()


def test_default_update_uses_aggregate_and_preferred_scheme_index(tmp_path, monkeypatch):
    thresholds = Path("tests/qualibact/thresholds_subset.csv").read_text(encoding="utf-8")
    index = json.dumps(
        {
            "species": [
                {
                    "species": "Escherichia coli",
                    "preferred_scheme": "qualibact-v1.0",
                }
            ]
        }
    )
    requested = []

    class MockResponse:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            return None

    def fake_get(url, **_kwargs):
        requested.append(url)
        return MockResponse(index if url == QUALIBACT_INDEX_URL else thresholds)

    monkeypatch.setattr("speccheck.update_criteria.requests.get", fake_get)
    assert update_criteria_file(
        tmp_path / "criteria.csv",
        snapshot_dir=tmp_path / "snapshot",
    )
    assert requested == [QUALIBACT_DEFAULT_URL, QUALIBACT_INDEX_URL]
