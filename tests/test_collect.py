import csv
import os

import pytest

from speccheck.collect import (
    check_criteria,
    collect_files,
    criteria_applies_to_software,
    write_to_file,
)
from speccheck.main import _add_parser_aliases, _filter_criteria_for_assembly_type


class MockModule:
    def __init__(self, filepath):
        self.filepath = filepath
        self.has_valid_filename = True
        self.has_valid_fileformat = True

    def fetch_values(self):
        return {"field1": "value1", "field2": "value2"}


class InvalidFilenameModule(MockModule):
    def __init__(self, filepath):
        super().__init__(filepath)
        self.has_valid_filename = False


class InvalidFileformatModule(MockModule):
    def __init__(self, filepath):
        super().__init__(filepath)
        self.has_valid_fileformat = False


def test_collect_files_valid():
    # Arrange
    all_files = ["file1.txt"]
    module_list = [MockModule]

    expected_output = {"MockModule": {"field1": "value1", "field2": "value2"}}

    # Act
    result = collect_files(all_files, module_list)

    # Assert
    assert result == expected_output


def test_collect_files_invalid_filename():
    # Arrange
    all_files = ["file1.txt", "file2.txt"]
    module_list = [InvalidFilenameModule]

    expected_output = {}

    # Act
    result = collect_files(all_files, module_list)

    # Assert
    assert result == expected_output


def test_collect_files_invalid_fileformat():
    # Arrange
    all_files = ["file1.txt", "file2.txt"]
    module_list = [InvalidFileformatModule]

    expected_output = {}

    # Act
    result = collect_files(all_files, module_list)

    # Assert
    assert result == expected_output


def test_collect_files_mixed_modules():
    # Arrange
    all_files = ["file1.txt"]
    module_list = [MockModule, InvalidFilenameModule, InvalidFileformatModule]

    expected_output = {"MockModule": {"field1": "value1", "field2": "value2"}}

    # Act
    result = collect_files(all_files, module_list)

    # Assert
    assert result == expected_output


def test_collect_files_rejects_duplicate_parser_matches():
    all_files = ["file1.txt", "file2.txt"]
    module_list = [MockModule]

    with pytest.raises(ValueError, match="Multiple files matched parser MockModule"):
        collect_files(all_files, module_list)


def test_write_to_file(tmp_path):
    # Arrange
    output_file = tmp_path / "output.csv"
    qc_report = {"field1": "value1", "field2": "value2"}

    # Act
    write_to_file(output_file, qc_report)

    # Assert
    assert output_file.exists()
    with open(output_file, encoding="utf-8") as f:
        content = f.read()
        assert content == "field1,field2\nvalue1,value2\n"


def test_write_to_file_creates_directories(tmp_path):
    # Arrange
    output_file = tmp_path / "nested/dir/output.csv"
    qc_report = {"field1": "value1", "field2": "value2"}

    # Act
    write_to_file(output_file, qc_report)

    # Assert
    assert output_file.exists()
    with open(output_file, encoding="utf-8") as f:
        content = f.read()
        assert content == "field1,field2\nvalue1,value2\n"


def test_write_to_file_overwrites_existing_file(tmp_path):
    # Arrange
    output_file = tmp_path / "output.csv"
    qc_report_initial = {"field1": "initial_value1", "field2": "initial_value2"}
    qc_report_new = {"field1": "new_value1", "field2": "new_value2"}

    # Act
    write_to_file(output_file, qc_report_initial)
    write_to_file(output_file, qc_report_new)

    # Assert
    assert output_file.exists()
    with open(output_file, encoding="utf-8") as f:
        content = f.read()
        assert content == "field1,field2\nnew_value1,new_value2\n"


def test_write_to_file_quotes_csv_values(tmp_path):
    output_file = tmp_path / "output.csv"
    qc_report = {"field1": 'value, with comma and "quotes"', "field2": "line1\nline2"}

    write_to_file(output_file, qc_report)

    with open(output_file, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows == [qc_report]


def test_depthparser_criteria_apply_to_depth_output():
    field = {
        "software": "DepthParser.short",
        "field": "Depth",
        "operator": ">",
        "value": 20,
    }
    assert criteria_applies_to_software("DepthParser.short", "Depth")
    assert check_criteria(field, {"Sample_id": "S1", "Read_type": "short", "Depth": 30.0})
    assert not check_criteria(field, {"Sample_id": "S1", "Read_type": "long", "Depth": 30.0})


def test_depthparser_criteria_select_matching_hybrid_row():
    field = {
        "software": "DepthParser.long",
        "field": "Depth",
        "operator": ">",
        "value": 20,
    }
    result = [
        {"Sample_id": "S1", "Read_type": "short", "Depth": 10.0},
        {"Sample_id": "S1", "Read_type": "long", "Depth": 25.0},
    ]
    assert check_criteria(field, result)


def test_checkm2_aliases_are_available_for_legacy_criteria_fields():
    recovered_values = {
        "Checkm": {
            "GC_Content": 50.4,
            "Genome_Size": 5100000,
            "Contig_N50": 120000,
            "Total_Contigs": 679,
        }
    }

    _add_parser_aliases(recovered_values)

    checkm = recovered_values["Checkm"]
    assert checkm["GC"] == 50.4
    assert checkm["Genome size (bp)"] == 5100000
    assert checkm["N50 (scaffolds)"] == 120000
    assert checkm["# contigs"] == 679


def test_filter_criteria_for_assembly_type():
    criteria = [
        {"assembly_type": "all", "field": "species"},
        {"assembly_type": "short", "field": "short_depth"},
        {"assembly_type": "long", "field": "long_depth"},
    ]

    assert [row["field"] for row in _filter_criteria_for_assembly_type(criteria, "all")] == [
        "species"
    ]
    assert [row["field"] for row in _filter_criteria_for_assembly_type(criteria, "short")] == [
        "species",
        "short_depth",
    ]
    assert [row["field"] for row in _filter_criteria_for_assembly_type(criteria, "long")] == [
        "species",
        "long_depth",
    ]
    assert [row["field"] for row in _filter_criteria_for_assembly_type(criteria, "hybrid")] == [
        "species",
        "short_depth",
        "long_depth",
    ]
