#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v pixi >/dev/null 2>&1; then
  export PATH="$HOME/.pixi/bin:$PATH"
fi

SAMPLE_ID="${1:-SAMN42765982}"
RUN_ROOT="${PWD}/.demo_work/ghru_ecoli_real/${SAMPLE_ID}"
READ_DIR="${RUN_ROOT}/reads"
IMAGE_DIR="${PWD}/.demo_work/ghru_images"
APPTAINER_CACHE="${PWD}/.demo_work/apptainer/cache"
APPTAINER_TMP="${PWD}/.demo_work/apptainer/tmp"
SHARED_SIF_DIR="${PWD}/../../../shared/singularity/GHRU-assembly"

mkdir -p "${READ_DIR}" "${IMAGE_DIR}" "${APPTAINER_CACHE}" "${APPTAINER_TMP}" "${RUN_ROOT}"

export APPTAINER_CACHEDIR="${APPTAINER_CACHE}"
export APPTAINER_TMPDIR="${APPTAINER_TMP}"
export SINGULARITY_CACHEDIR="${APPTAINER_CACHEDIR}"
export SINGULARITY_TMPDIR="${APPTAINER_TMPDIR}"

for image in \
  ariba_contam_0.1.1.sif \
  bash_ghru.sif \
  cgps_dragonflye_medaka.sif \
  fastqc_0.12.1--hdfd78af_0.sif \
  lrge_0.1.3--h9f13da3_1.sif \
  nanoplot_1.42.0--pyhdfd78af_0.sif \
  porechop_0.2.4--py310h84f13bb_8.sif \
  python.sif \
  quast_5.2.0--py312pl5321hc60241a_4.sif \
  shovill_1.1.0-2022Dec.sif \
  speccheck_0.2.1.sif \
  speciator_4.0.0.sif \
  sylph_0.1.0.sif \
  trimmomatic_0.36--3.sif \
  unicycler_0.5.0--py39heaaa4ec_5.sif
do
  ln -sfn "${SHARED_SIF_DIR}/${image}" "${IMAGE_DIR}/${image}"
done

CHECKM2_IMAGE="${IMAGE_DIR}/checkm2_0.1.0.sif"
if [[ ! -f "${CHECKM2_IMAGE}" ]]; then
  apptainer pull "${CHECKM2_IMAGE}" docker://happykhan/checkm2:0.1.0
fi

ENA_URL="https://www.ebi.ac.uk/ena/portal/api/filereport?accession=${SAMPLE_ID}&result=read_run&fields=run_accession,fastq_ftp,fastq_md5,library_layout,sample_accession,scientific_name&format=tsv"
ENA_TSV="${RUN_ROOT}/ena.tsv"
curl -fsSL "${ENA_URL}" -o "${ENA_TSV}"

RUN_ACCESSION="$(tail -n +2 "${ENA_TSV}" | cut -f1)"
FASTQ_FTPS="$(tail -n +2 "${ENA_TSV}" | cut -f2)"
SCIENTIFIC_NAME="$(tail -n +2 "${ENA_TSV}" | cut -f6)"

if [[ -z "${RUN_ACCESSION}" || -z "${FASTQ_FTPS}" ]]; then
  echo "Failed to resolve ENA FASTQ links for ${SAMPLE_ID}" >&2
  exit 1
fi

if [[ "${SCIENTIFIC_NAME}" != "Escherichia coli" ]]; then
  echo "Resolved sample ${SAMPLE_ID} is not Escherichia coli: ${SCIENTIFIC_NAME}" >&2
  exit 1
fi

IFS=';' read -r FASTQ1_URL FASTQ2_URL <<< "${FASTQ_FTPS}"
FASTQ1_NAME="$(basename "${FASTQ1_URL}")"
FASTQ2_NAME="$(basename "${FASTQ2_URL}")"
FASTQ1_PATH="${READ_DIR}/${FASTQ1_NAME}"
FASTQ2_PATH="${READ_DIR}/${FASTQ2_NAME}"

if [[ ! -f "${FASTQ1_PATH}" ]]; then
  curl -fL "https://${FASTQ1_URL}" -o "${FASTQ1_PATH}"
fi
if [[ ! -f "${FASTQ2_PATH}" ]]; then
  curl -fL "https://${FASTQ2_URL}" -o "${FASTQ2_PATH}"
fi

cat > "${RUN_ROOT}/samplesheet.csv" <<EOF
sample_id,short_reads1,short_reads2,long_reads,genome_size
${SAMPLE_ID},${FASTQ1_PATH},${FASTQ2_PATH},,
EOF

echo "Staged real E. coli GHRU sample ${SAMPLE_ID} (${RUN_ACCESSION}) in ${RUN_ROOT}"
