#!/usr/bin/env bash
#SBATCH --job-name=speccheck-upstream
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <sample_id> <assembly_fasta> <output_dir> [reads_1.fastq.gz reads_2.fastq.gz]"
  exit 1
fi

SAMPLE_ID="$1"
ASSEMBLY_FASTA="$2"
OUTPUT_DIR="$3"
READS_1="${4:-}"
READS_2="${5:-}"

mkdir -p "${OUTPUT_DIR}/${SAMPLE_ID}" logs
SAMPLE_DIR="${OUTPUT_DIR}/${SAMPLE_ID}"

echo "Running upstream QC for ${SAMPLE_ID}"
echo "Assembly: ${ASSEMBLY_FASTA}"
echo "Output: ${SAMPLE_DIR}"

# Load or activate the environment that provides the upstream tools.
# Examples:
# module load quast checkm ariba
# source /path/to/conda/bin/activate upstream-qc

# QUAST
if command -v quast.py >/dev/null 2>&1; then
  quast.py "${ASSEMBLY_FASTA}" -o "${SAMPLE_DIR}/quast"
  cp "${SAMPLE_DIR}/quast/report.tsv" "${SAMPLE_DIR}/${SAMPLE_ID}.short.report.tsv"
else
  echo "quast.py not found; skipping QUAST"
fi

# CheckM
if command -v checkm >/dev/null 2>&1; then
  checkm lineage_wf -x fa "$(dirname "${ASSEMBLY_FASTA}")" "${SAMPLE_DIR}/checkm_wf"
  checkm qa "${SAMPLE_DIR}/checkm_wf/lineage.ms" "${SAMPLE_DIR}/checkm_wf" -o 2 \
    > "${SAMPLE_DIR}/${SAMPLE_ID}_qc_summary.tsv"
else
  echo "checkm not found; skipping CheckM"
fi

# Speciator and Sylph are environment-specific in most labs.
# Replace the following placeholders with your site-specific commands.
if [[ -n "${READS_1}" && -n "${READS_2}" ]]; then
  echo "Add your Speciator command here and write:"
  echo "  ${SAMPLE_DIR}/${SAMPLE_ID}.short.tsv"
  echo "Add your Sylph command here and write:"
  echo "  ${SAMPLE_DIR}/${SAMPLE_ID}_slyph_report.tsv"
  echo "Add your ARIBA command here and write:"
  echo "  ${SAMPLE_DIR}/${SAMPLE_ID}_mlst_report.details.tsv"
else
  echo "Reads not supplied; skipping read-based tools"
fi

echo "Upstream QC template completed for ${SAMPLE_ID}"
echo "Run speccheck collect on ${SAMPLE_DIR} once the expected files exist."
