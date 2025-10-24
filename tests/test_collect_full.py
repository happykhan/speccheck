import os
from speccheck.main import collect


def test_collect():

    # Define the input filepaths
    input_filepaths = ["tests/collect_test_data"]
    criteria_file = "criteria.csv"
    output_file = "collect_output.csv"

    sample_id = "Sample1"
    # Run the collect function
    collect("Mycoplasma genitalium", input_filepaths, criteria_file, output_file, sample_id)

    # Check if the output file is created
    assert os.path.isfile(output_file)

    # Check the content of the output file
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Sample1" in content
        assert "Quast.N50.check" in content
    os.remove(output_file)
