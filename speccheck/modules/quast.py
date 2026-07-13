"""
Quast class for handling QUAST quality control format files.
This class inherits from QualityControlFormat and provides methods to validate
the file format and fetch values from the file.
Methods
-------
has_valid_fileformat():
    Checks if the file has a valid QUAST format by comparing each line with
    expected regular expressions.
fetch_values():
    Reads the file and returns a dictionary of key-value pairs extracted from
    the file.
Attributes
----------
file_path : str
    Path to the QUAST file to be processed.
"""


class Quast:
    """
    A class to represent and validate the QUAST (Quality Assessment Tool for Genome Assemblies) report format.
    Methods
    -------
    has_valid_fileformat():
        Checks if the file at `self.file_path` adheres to the expected QUAST report format.
    fetch_values():
        Parses the QUAST report file and returns a dictionary of key-value pairs from the report.
    """

    def __init__(self, file_path):
        """
        Parameters
        ----------
        file_path : str
            The path to the QUAST report file.
        """
        self.file_path = file_path

    @property
    def has_valid_filename(self):
        return self.file_path.endswith("report.tsv")

    @property
    def has_valid_fileformat(self):
        try:
            values = self.fetch_values()
        except ValueError:
            return False
        required_keys = {
            "Assembly",
            "# contigs (>= 0 bp)",
            "Total length (>= 0 bp)",
            "GC (%)",
            "N50",
        }
        return required_keys.issubset(values)

    def fetch_values(self):
        with open(self.file_path, encoding="utf-8") as file:
            lines = file.readlines()

        values = {}
        for line in lines:
            if not line.strip():
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 2:
                raise ValueError(f"QUAST report row must contain exactly two columns: {line!r}")
            key, value = parts
            # A float will have a decimal point, so we try to convert the value to float
            if "." in value and value.replace(".", "").isdigit():
                value = float(value)
            # If the value is not a float, we try to convert it to an integer
            elif value.isdigit():
                value = int(value)
            values[key] = value
            if key == "# N's per 100 kbp":
                values["Ns per 100 kbp"] = value

        return values
