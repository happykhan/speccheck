# Quick Start

This page assumes you already have QC output files from upstream tools.

## 1. See what Speccheck can read

```bash
speccheck inspect path/to/qc_outputs/
speccheck modules
```

`inspect` does not write outputs. Use it before `collect`, especially when you
are connecting a new workflow.

## 2. Collect one sample

```bash
mkdir -p qc_collect

speccheck collect path/to/qc_outputs/SAMPLE_001/ \
  --sample SAMPLE_001 \
  --organism "Escherichia coli" \
  --assembly-type short \
  --output-file qc_collect/SAMPLE_001.csv
```

The output CSV contains:

- parsed metrics, for example `Quast.N50` or `Checkm.Contamination`;
- status/check columns from the criteria CSV;
- provenance, including Speccheck version and criteria checksum.

## 3. Collect many samples

For a directory-per-sample layout:

```bash
mkdir -p qc_collect

for sample_dir in path/to/run/*; do
  sample="$(basename "$sample_dir")"
  speccheck collect "$sample_dir" \
    --sample "$sample" \
    --organism "Escherichia coli" \
    --assembly-type short \
    --output-file "qc_collect/${sample}.csv"
done
```

If the organism is not supplied, Speccheck tries to infer it from parser outputs
configured as species fields in the criteria file. If no single species can be
resolved, collection stops by default. Use `--allow-unknown-organism` only when
generic fallback thresholds are the intended policy.

## 4. Build the report

```bash
speccheck summary qc_collect \
  --output qc_report \
  --plot \
  --xlsx-output qc_report/report.xlsx
```

Outputs:

| File | Use |
| --- | --- |
| `report.csv` | compact merged result for review and downstream scripts |
| `report.full.csv` | wide table with parser, metadata, and provenance columns |
| `report.html` | interactive human review report |
| `report.xlsx` | optional workbook with summary and full sheets |

## 5. Read the first three columns

Start with:

- `overall_qc`: `PASS`, `WARN`, `FAIL`, or `NOT_EVALUATED`;
- `all_checks_passed`: binary convenience value;
- `reason_summary`: compact explanation of warnings, failures, and missing
  checks.

`NOT_EVALUATED` means Speccheck expected a metric from the selected criteria but
could not find it in the parsed input. It is not the same as failing a threshold.

## 6. Pipeline layout shortcut

For a published workflow output layout such as GHRU Assembly:

```bash
speccheck collect-pipeline results/ qc_collect \
  --layout ghru \
  --organism "Escherichia coli" \
  --work-dir work/

speccheck summary qc_collect --output qc_report --plot
```

See [Pipeline Integration](ghru.md) for details.
