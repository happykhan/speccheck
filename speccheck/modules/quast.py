"""Parse native QUAST report.tsv files in wide or transposed form."""

import csv

from speccheck.modules.base import Parser, parse_scalar


class Quast(Parser):
    software_name = "Quast"
    description = "QUAST assembly report"
    supported_filenames = "*report.tsv in native wide or transposed form"
    required_keys = {
        "Assembly",
        "# contigs (>= 0 bp)",
        "Total length (>= 0 bp)",
        "GC (%)",
        "N50",
    }

    @property
    def has_valid_filename(self):
        return self.file_path.endswith("report.tsv") or self.file_path.endswith(".tsv")

    @property
    def has_valid_fileformat(self):
        try:
            return self.required_keys.issubset(self.fetch_values())
        except (OSError, UnicodeError, csv.Error, ValueError):
            return False

    def fetch_values(self):
        with open(self.file_path, encoding="utf-8", newline="") as handle:
            rows = [
                row
                for row in csv.reader(handle, delimiter="\t")
                if any(cell.strip() for cell in row)
            ]
        if not rows:
            raise ValueError("QUAST report is empty.")
        if len(rows) == 2 and len(rows[0]) > 2:
            if len(rows[0]) != len(rows[1]):
                raise ValueError("QUAST wide report header and value row have different widths.")
            values = dict(zip(rows[0], map(parse_scalar, rows[1]), strict=True))
        else:
            if any(len(row) != 2 for row in rows):
                raise ValueError("QUAST transposed report rows must contain exactly two columns.")
            values = {key: parse_scalar(value) for key, value in rows}
        if "# N's per 100 kbp" in values:
            values["Ns per 100 kbp"] = values["# N's per 100 kbp"]
        return values
