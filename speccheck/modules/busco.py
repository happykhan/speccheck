"""Parser for BUSCO short-summary text files."""

from __future__ import annotations

import re
from pathlib import Path

from speccheck.modules.base import Parser

_SUMMARY_RE = re.compile(
    r"C:(?P<Complete>[0-9.]+)%\[S:(?P<Single_copy>[0-9.]+)%,D:(?P<Duplicated>[0-9.]+)%\],"
    r"F:(?P<Fragmented>[0-9.]+)%,M:(?P<Missing>[0-9.]+)%,n:(?P<Total>[0-9]+)"
)


class Busco(Parser):
    software_name = "Busco"
    description = "BUSCO complete, duplicated, fragmented, and missing orthologue percentages"
    supported_filenames = "short_summary*.txt produced by BUSCO"

    @property
    def has_valid_filename(self) -> bool:
        name = Path(self.file_path).name
        return name.startswith("short_summary") and name.endswith(".txt")

    def _text(self) -> str:
        return Path(self.file_path).read_text(encoding="utf-8")

    @property
    def has_valid_fileformat(self) -> bool:
        try:
            return _SUMMARY_RE.search(self._text()) is not None
        except (OSError, UnicodeError):
            return False

    def fetch_values(self) -> dict:
        text = self._text()
        match = _SUMMARY_RE.search(text)
        if match is None:
            raise ValueError(f"BUSCO summary line not found in {self.file_path}")
        values = {
            key: int(value) if key == "Total" else float(value)
            for key, value in match.groupdict().items()
        }
        lineage = re.search(r"(?:lineage_dataset|The lineage dataset is):?\s*([^\s#]+)", text)
        values["Lineage"] = lineage.group(1) if lineage else ""
        return values
