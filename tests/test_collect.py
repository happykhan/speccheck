import pytest
import os
from speccheck.collect import collect_files, write_to_file

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
    all_files = ["file1.txt", "file2.txt"]
    module_list = [MockModule]

    expected_output = {
        "MockModule": {"field1": "value1", "field2": "value2"}
    }

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
    all_files = ["file1.txt", "file2.txt"]
    module_list = [MockModule, InvalidFilenameModule, InvalidFileformatModule]

    expected_output = {
        "MockModule": {"field1": "value1", "field2": "value2"}
    }

    # Act
    result = collect_files(all_files, module_list)

    # Assert
    assert result == expected_output

def test_write_to_file(tmp_path):
    # Arrange
    output_file = tmp_path / "output.csv"
    qc_report = {"field1": "value1", "field2": "value2"}

    # Act
    write_to_file(output_file, qc_report)

    # Assert
    assert output_file.exists()
    with open(output_file, "r", encoding="utf-8") as f:
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
    with open(output_file, "r", encoding="utf-8") as f:
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
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert content == "field1,field2\nnew_value1,new_value2\n"