#!/usr/bin/env bash
#SBATCH --job-name=speccheck-ecoli-demo
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=.demo_work/slurm/speccheck-ecoli-demo.%j.out
#SBATCH --error=.demo_work/slurm/speccheck-ecoli-demo.%j.err

set -euo pipefail

cd "${SLURM_SUBMIT_DIR:-$PWD}"
mkdir -p .demo_work/slurm

if ! command -v pixi >/dev/null 2>&1; then
  export PATH="$HOME/.pixi/bin:$PATH"
fi

if [[ ! -d .demo_work/qc_venv ]]; then
  python3.11 -m venv .demo_work/qc_venv
  . .demo_work/qc_venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install quast
else
  . .demo_work/qc_venv/bin/activate
fi

python -m pip install -e ".[dev]"

python scripts/build_qualibact_ecoli_demo.py \
  --work-dir .demo_work/qualibact_ecoli_real \
  --output-dir examples/qualibact_ecoli/real_panel/report \
  --atbfetcher-dir .demo_work/atbfetcher \
  --threads "${SLURM_CPUS_PER_TASK:-4}"
