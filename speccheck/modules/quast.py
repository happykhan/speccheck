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

import re


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
        with open(self.file_path, encoding="utf-8") as file:
            first_line = file.readline()
            if "\t" not in first_line:
                return False

        with open(self.file_path, encoding="utf-8") as file:
            lines = file.readlines()
            lines = [line for line in lines if line.strip()]
        expected_lines = [
            r"Assembly\t+\S+",
            r"# contigs \(>= 0 bp\)\t+\d+",
            r"# contigs \(>= 1000 bp\)\t+\d+",
            r"# contigs \(>= 5000 bp\)\t+\d+",
            r"# contigs \(>= 10000 bp\)\t+\d+",
            r"# contigs \(>= 25000 bp\)\t+\d+",
            r"# contigs \(>= 50000 bp\)\t+\d+",
            r"Total length \(>= 0 bp\)\t+\d+",
            r"Total length \(>= 1000 bp\)\t+\d+",
            r"Total length \(>= 5000 bp\)\t+\d+",
            r"Total length \(>= 10000 bp\)\t+\d+",
            r"Total length \(>= 25000 bp\)\t+\d+",
            r"Total length \(>= 50000 bp\)\t+\d+",
            r"# contigs\t+\d+",
            r"Largest contig\t+\d+",
            r"Total length\t+\d+",
            r"GC \(\%\)\t+\d+\.\d+",
            r"N50\t+\d+",
            r"N90\t+\d+",
            r"auN\t+\d+\.\d+",
            r"L50\t+\d+",
            r"L90\t+\d+",
            r"# N's per 100 kbp\t+\d+\.\d+",
        ]

        if len(lines) != len(expected_lines):
            return False

        for line, pattern in zip(lines, expected_lines, strict=False):
            if not re.match(pattern, line.strip()):
                return False

        return True

    def fetch_values(self):
        with open(self.file_path, encoding="utf-8") as file:
            lines = file.readlines()

        values = {}
        for line in lines:
            key, value = line.strip().split("\t")
            # A float will have a decimal point, so we try to convert the value to float
            if "." in value and value.replace(".", "").isdigit():
                value = float(value)
            # If the value is not a float, we try to convert it to an integer
            elif value.isdigit():
                value = int(value)
            values[key] = value

        return values
