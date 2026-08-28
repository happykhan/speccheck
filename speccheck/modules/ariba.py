import csv

from speccheck.modules.base import Parser


class Ariba(Parser):
    software_name = "Ariba"
    description = "ARIBA MLST/contamination summary"
    supported_filenames = "TSV with gene, allele, coverage, and heterozygosity columns"
    required_headers = {"gene", "allele", "cov", "pc", "ctgs", "depth", "hetmin", "hets"}

    @property
    def has_valid_filename(self):
        return self.file_path.endswith(".tsv")

    @property
    def has_valid_fileformat(self):

        try:
            with open(self.file_path, encoding="utf-8", newline="") as file:
                headers = csv.DictReader(file, delimiter="\t").fieldnames or []
        except (OSError, UnicodeError, csv.Error):
            return False
        return self.required_headers.issubset(headers)

    def fetch_values(self):
        with open(self.file_path, encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter="\t")
            result = {"passed": 0, "total": 0, "percent": 0, "not_called": 0}
            for row in reader:
                # if allele does not have * or , then passed
                if "*" not in row["allele"] and row["allele"] not in ["ND"]:
                    result["passed"] += 1
                if row["allele"] in ["ND"]:
                    result["not_called"] += 1
                result["total"] += 1
            result["percent"] = result["passed"] / result["total"] * 100 if result["total"] else 0.0
        return result
