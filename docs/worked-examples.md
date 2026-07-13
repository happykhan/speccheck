# Worked Examples

## Example 1: one sample, explicit species

```bash
speccheck inspect sample_qc/

speccheck collect sample_qc/ \
  --sample SAMPLE_001 \
  --organism "Escherichia coli" \
  --assembly-type short \
  --output-file qc_collect/SAMPLE_001.csv

speccheck summary qc_collect --output qc_report --plot
```

Use this pattern for ad hoc review or small batches where files are already
grouped by sample.

## Example 2: strict mode for missing expected metrics

By default, missing expected metrics are reported as `NOT_EVALUATED` but do not
automatically fail the sample. For a stricter release or CI-style check:

```bash
speccheck collect sample_qc/ \
  --sample SAMPLE_001 \
  --organism "Escherichia coli" \
  --fail-on-not-evaluated \
  --output-file qc_collect/SAMPLE_001.csv
```

Use this when incomplete evidence should block a sample.

## Example 3: after a GHRU Assembly run

```bash
speccheck collect-pipeline ghru_output/ qc_collect \
  --layout ghru \
  --organism "Escherichia coli" \
  --work-dir ghru_work/

speccheck summary qc_collect \
  --output qc_report \
  --plot \
  --xlsx-output qc_report/report.xlsx
```

The GHRU layout collector looks for published QUAST, CheckM2, Speciator, Sylph,
ARIBA, and depth outputs. The `--work-dir` option is useful only when the
workflow did not publish a compact depth file.

## Example 4: use a project criteria file

Copy the packaged criteria file, edit it, and use the edited copy:

```bash
python - <<'PY'
from pathlib import Path
from speccheck.criteria import get_default_criteria_path

Path("project_criteria.csv").write_text(
    Path(get_default_criteria_path()).read_text(),
    encoding="utf-8",
)
PY

speccheck check --criteria-file project_criteria.csv

speccheck collect sample_qc/ \
  --sample SAMPLE_001 \
  --criteria-file project_criteria.csv \
  --output-file qc_collect/SAMPLE_001.csv
```

Add project rows with a clear `source`, for example `project-local`.

## Example 5: reproduce the committed 100-sample summaries

The compact example outputs are committed under
`examples/qualibact_ecoli/real_run_100/`.

Regenerate the derived analysis tables and figures:

```bash
pixi run python scripts/create_real_run_100_assets.py
```

This uses the committed report files and writes:

- concordance table;
- discordant sample table;
- metric distribution table;
- figures;
- provenance summary JSON.

See [100-sample E. coli case study](case-study.md) for interpretation.
