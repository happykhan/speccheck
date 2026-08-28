"""Parsers for the one-row CheckM and CheckM2 tabular reports used by GHRU."""

import csv

from speccheck.modules.base import Parser, parse_scalar


class Checkm(Parser):
    software_name = "Checkm"
    description = "CheckM or CheckM2 completeness, contamination, and assembly metrics"
    supported_filenames = "One-row CheckM or CheckM2 TSV quality report"

    checkm2_required = {"Name", "Completeness", "Contamination", "Genome_Size"}
    checkm1_required = {
        "Bin Id",
        "Completeness",
        "Contamination",
        "Genome size (bp)",
        "GC",
        "# contigs",
        "N50 (scaffolds)",
        "# predicted genes",
    }

    @property
    def has_valid_filename(self):
        return self.file_path.endswith(".tsv")

    def _rows(self):
        with open(self.file_path, encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle, delimiter="\t"))

    @property
    def has_valid_fileformat(self):
        try:
            with open(self.file_path, encoding="utf-8", newline="") as handle:
                headers = set(csv.DictReader(handle, delimiter="\t").fieldnames or [])
        except (OSError, UnicodeError, csv.Error):
            return False
        return self.checkm2_required.issubset(headers) or self.checkm1_required.issubset(headers)

    def fetch_values(self):
        rows = self._rows()
        if len(rows) != 1:
            raise ValueError("CheckM report must contain exactly one row of values.")
        parsed = {key: parse_scalar(value) for key, value in rows[0].items() if value is not None}
        legacy_map = {
            "Bin Id": "Name",
            "Genome size (bp)": "Genome_Size",
            "GC": "GC_Content",
            "# contigs": "Total_Contigs",
            "N50 (scaffolds)": "Contig_N50",
            "# predicted genes": "Total_Coding_Sequences",
            "Longest contig (bp)": "Max_Contig_Length",
            "Coding density": "Coding_Density",
            "Translation table": "Translation_Table_Used",
        }
        for source, target in legacy_map.items():
            if source in parsed:
                parsed[target] = parsed[source]
        gc_content = parsed.get("GC_Content")
        if isinstance(gc_content, (int, float)) and 0 <= gc_content <= 1:
            parsed["GC_Content"] = gc_content * 100
        return parsed
