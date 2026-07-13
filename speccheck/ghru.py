import logging
import os
import re
from dataclasses import dataclass, field


_ASSEMBLY_RE = re.compile(r"^(?P<sample>.+)\.(?P<assembly>short|long|hybrid)\.tsv$")
_QUAST_RE = re.compile(r"^ori_(?P<sample>.+)\.(?P<assembly>short|long|hybrid)\.report\.tsv$")
_SYLPH_RE = re.compile(r"^(?P<sample>.+)_slyph_report\.tsv$")
_ARIBA_RE = re.compile(r"^(?P<sample>.+)_mlst_report\.details\.tsv$")
_DEPTH_RE = re.compile(
    r"^(?P<sample>.+)\.(?P<assembly>short|long|hybrid)(?P<read_type>short_reads|long_reads)?\.depth\.tsv$"
)


@dataclass
class GhruSampleFiles:
    sample_id: str
    assembly_type: str | None = None
    files: list[str] = field(default_factory=list)

    def add_file(self, path: str, assembly_type: str | None = None) -> None:
        if path not in self.files:
            self.files.append(path)
        if assembly_type:
            if self.assembly_type and self.assembly_type != assembly_type:
                raise ValueError(
                    f"Sample {self.sample_id} has conflicting assembly types: "
                    f"{self.assembly_type} vs {assembly_type}"
                )
            self.assembly_type = assembly_type


def discover_ghru_sample_files(output_dir: str, work_dir: str | None = None) -> dict[str, GhruSampleFiles]:
    """Discover parsable upstream GHRU outputs grouped by sample."""
    output_dir = os.path.abspath(output_dir)
    work_dir = os.path.abspath(work_dir) if work_dir else None

    sample_map: dict[str, GhruSampleFiles] = {}

    def ensure_sample(sample_id: str) -> GhruSampleFiles:
        if sample_id not in sample_map:
            sample_map[sample_id] = GhruSampleFiles(sample_id=sample_id)
        return sample_map[sample_id]

    def add_with_match(path: str, sample_id: str, assembly_type: str | None = None) -> None:
        ensure_sample(sample_id).add_file(path, assembly_type)

    walkers = [(output_dir, False)]
    if work_dir and os.path.isdir(work_dir):
        walkers.append((work_dir, True))

    for root_dir, depth_only in walkers:
        for root, _dirs, files in os.walk(root_dir):
            for filename in files:
                path = os.path.join(root, filename)
                if not filename.endswith(".tsv"):
                    continue

                if depth_only:
                    match = _DEPTH_RE.match(filename)
                    if match:
                        add_with_match(path, match.group("sample"), match.group("assembly"))
                    continue

                match = _QUAST_RE.match(filename)
                if match:
                    add_with_match(path, match.group("sample"), match.group("assembly"))
                    continue

                match = _ASSEMBLY_RE.match(filename)
                if match:
                    parent = os.path.basename(os.path.dirname(path))
                    if parent in {"checkm_summary", "speciation_summary"}:
                        add_with_match(path, match.group("sample"), match.group("assembly"))
                    continue

                match = _SYLPH_RE.match(filename)
                if match and os.path.basename(os.path.dirname(path)) == "sylph_summary":
                    add_with_match(path, match.group("sample"))
                    continue

                match = _ARIBA_RE.match(filename)
                if match and os.path.basename(os.path.dirname(path)) == "ariba_summary":
                    add_with_match(path, match.group("sample"))
                    continue

                match = _DEPTH_RE.match(filename)
                if match:
                    add_with_match(path, match.group("sample"), match.group("assembly"))
                    continue

    if not sample_map:
        raise ValueError(f"No GHRU-compatible sample outputs found under {output_dir}")

    for sample in sample_map.values():
        sample.files.sort()
        if not sample.assembly_type:
            logging.warning(
                "Could not infer assembly type for sample %s from discovered GHRU outputs.",
                sample.sample_id,
            )
    return sample_map
