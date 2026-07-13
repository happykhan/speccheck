from speccheck.modules.busco import Busco


def test_busco_detects_and_parses_short_summary():
    parser = Busco("tests/busco/short_summary.test.txt")

    assert parser.has_valid_filename
    assert parser.has_valid_fileformat
    assert parser.fetch_values() == {
        "Complete": 98.7,
        "Single_copy": 98.0,
        "Duplicated": 0.7,
        "Fragmented": 0.4,
        "Missing": 0.9,
        "Total": 124,
        "Lineage": "bacteria_odb10",
    }


def test_busco_rejects_other_text(tmp_path):
    path = tmp_path / "short_summary.invalid.txt"
    path.write_text("not a BUSCO report", encoding="utf-8")

    assert not Busco(path).has_valid_fileformat
