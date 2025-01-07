import os
import pytest
from speccheck.main import collect

@pytest.fixture
def setup_files(tmp_path):
    # Create temporary input files
    input_filepaths = []
    for i in range(3):
        file_path = tmp_path / f"input_file_{i}.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Sample data {i}")
        input_filepaths.append(file_path)
    
    # Create a temporary criteria file
    criteria_file = tmp_path / "criteria.csv"    
    with open(criteria_file, "w", encoding="utf-8") as f:
        f.write("assembly_type,software,field,operator,value,species,special_field\n")
        f.write("type1,software1,field1,>=,10,all,\n")
    
    # Create a temporary output file
    output_file = tmp_path / "output.csv"
    
    return input_filepaths, criteria_file, output_file

def test_collect(setup_files):
    input_filepaths, criteria_file, output_file = setup_files
    sample_name = "Sample1"
    
    # Run the collect function
    collect("organism1", input_filepaths, criteria_file, output_file, sample_name)
    
    # Check if the output file is created
    assert os.path.isfile(output_file)
    
    # Check the content of the output file
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Sample1" in content
        assert "software1.field1.check" in content