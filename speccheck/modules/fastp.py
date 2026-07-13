"""Parser for the machine-readable JSON report produced by fastp."""

from __future__ import annotations

import json
from pathlib import Path

from speccheck.modules.base import Parser


class Fastp(Parser):
    software_name = "Fastp"
    description = "fastp short-read quality metrics before and after filtering"
    supported_filenames = "*.json containing fastp summary.before_filtering/after_filtering"

    @property
    def has_valid_filename(self) -> bool:
        return self.file_path.lower().endswith(".json")

    def _load(self):
        with open(self.file_path, encoding="utf-8") as handle:
            return json.load(handle)

    @property
    def has_valid_fileformat(self) -> bool:
        try:
            report = self._load()
        except (OSError, UnicodeError, json.JSONDecodeError):
            return False
        summary = report.get("summary", {})
        return all(name in summary for name in ("before_filtering", "after_filtering"))

    def fetch_values(self) -> dict:
        report = self._load()
        summary = report["summary"]
        values = {
            "report": Path(self.file_path).name,
            "version": summary.get("fastp_version", ""),
            "sequencing": summary.get("sequencing", ""),
        }
        for stage in ("before_filtering", "after_filtering"):
            for metric, value in summary.get(stage, {}).items():
                values[f"{stage}_{metric}"] = value
        values["duplication_rate"] = report.get("duplication", {}).get("rate")
        passed = report.get("filtering_result", {}).get("passed_filter_reads")
        total = summary.get("before_filtering", {}).get("total_reads")
        values["passed_filter_rate"] = passed / total if passed is not None and total else None
        return values
