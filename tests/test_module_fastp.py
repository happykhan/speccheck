from speccheck.modules.fastp import Fastp


def test_fastp_detects_and_parses_machine_readable_report():
    parser = Fastp("tests/fastp/fastp_test.json")

    assert parser.has_valid_filename
    assert parser.has_valid_fileformat
    values = parser.fetch_values()
    assert values["before_filtering_q30_rate"] == 0.906494
    assert values["after_filtering_q30_rate"] == 0.906494
    assert values["passed_filter_rate"] == 1.0


def test_fastp_rejects_non_fastp_json(tmp_path):
    path = tmp_path / "other.json"
    path.write_text('{"summary": {}}', encoding="utf-8")

    assert not Fastp(path).has_valid_fileformat
