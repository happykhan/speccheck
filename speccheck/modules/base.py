"""Small parser contracts and reusable delimited-file helpers."""

from __future__ import annotations

import csv
from abc import ABC, abstractmethod


def parse_scalar(value):
    """Convert a delimited text value to an int/float when possible."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text) if "." in text or "e" in text.lower() else int(text)
    except ValueError:
        return text


class Parser(ABC):
    """Contract implemented by every Speccheck input parser."""

    software_name: str | None = None
    description = ""
    supported_filenames = ""

    def __init__(self, file_path):
        self.file_path = str(file_path)

    @property
    @abstractmethod
    def has_valid_filename(self) -> bool:
        """Return whether the path could belong to this parser."""

    @property
    @abstractmethod
    def has_valid_fileformat(self) -> bool:
        """Return whether the file content matches this parser."""

    @abstractmethod
    def fetch_values(self) -> dict | list[dict]:
        """Return normalized metric values."""


class SingleRowTsvParser(Parser):
    """Reusable parser for a one-record TSV with known required headers."""

    required_headers: tuple[str, ...] = ()
    exact_headers = True

    @property
    def has_valid_filename(self) -> bool:
        return self.file_path.endswith(".tsv")

    @property
    def has_valid_fileformat(self) -> bool:
        try:
            with open(self.file_path, encoding="utf-8", newline="") as handle:
                headers = csv.DictReader(handle, delimiter="\t").fieldnames or []
        except (OSError, UnicodeError, csv.Error):
            return False
        if self.exact_headers:
            return headers == list(self.required_headers)
        return set(self.required_headers).issubset(headers)

    def fetch_values(self) -> dict:
        with open(self.file_path, encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        if len(rows) != 1:
            raise ValueError("The file must contain exactly one row of values.")
        return {key: parse_scalar(value) for key, value in rows[0].items() if value is not None}
