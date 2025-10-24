import csv


class Depth:
    """
    Parser for depth.tsv files.
    Handles three types:
      1. Short-read only   → one row, Read_type = short
      2. Long-read only    → one row, Read_type = long
      3. Hybrid            → two rows, Read_type = short & long
    """

    def __init__(self, file_path):
        self.file_path = file_path

    @property
    def has_valid_filename(self):
        """Check if the file name ends with .tsv"""
        return self.file_path.endswith(".tsv")

    @property
    def has_valid_fileformat(self):
        """Check if file has required headers"""
        required_headers = ["Sample_id", "Read_type", "Depth"]
        try:
            with open(self.file_path, encoding="utf-8") as file:
                reader = csv.DictReader(file, delimiter="\t")
                headers = reader.fieldnames
                if not headers:
                    return False
                return all(h in headers for h in required_headers)
        except Exception:
            return False

    def fetch_values(self):
        """Read the file and return parsed rows (dict or list)."""
        with open(self.file_path, encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter="\t")
            rows = list(reader)

            # Check for empty file
            if not rows:
                raise ValueError("The file is empty.")

            parsed_rows = []

            for row in rows:
                parsed_row = {}
                for key, value in row.items():
                    if value is None or value.strip() == "":
                        parsed_row[key] = None
                        continue
                    value = value.strip()

                    if key == "Depth":
                        try:
                            parsed_row[key] = float(value)
                        except ValueError:
                            parsed_row[key] = value
                    else:
                        parsed_row[key] = value

                parsed_rows.append(parsed_row)

            # Validate based on row count and read types
            if len(parsed_rows) == 1:
                read_type = parsed_rows[0].get("Read_type", "").lower()
                if read_type not in ("short", "long"):
                    raise ValueError("Invalid Read_type. Must be 'short' or 'long'.")
                return parsed_rows[0]

            elif len(parsed_rows) == 2:
                read_types = {r.get("Read_type", "").lower() for r in parsed_rows}
                if read_types != {"short", "long"}:
                    raise ValueError("Hybrid file must contain one 'short' and one 'long' row.")
                return parsed_rows

            else:
                raise ValueError("File must contain either one or two rows (short/long or hybrid).")
