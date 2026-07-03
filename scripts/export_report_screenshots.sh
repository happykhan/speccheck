#!/usr/bin/env bash
set -euo pipefail

output_dir="${1:-examples/qualibact_ecoli/figures}"
mkdir -p "$output_dir"

repo_root="$(pwd)"

capture_with_chromium() {
  local browser="$1"
  local html_path="$2"
  local output_path="$3"
  local height="$4"
  "$browser" \
    --headless \
    --disable-gpu \
    --hide-scrollbars \
    --window-size="1600,${height}" \
    --screenshot="$output_path" \
    "file://${repo_root}/${html_path}"
}

capture_with_firefox() {
  local html_path="$1"
  local output_path="$2"
  local height="$3"
  local profile_dir
  profile_dir="$(mktemp -d /tmp/speccheck-firefox-profile.XXXXXX)"
  firefox \
    --headless \
    --profile "$profile_dir" \
    --window-size="1600,${height}" \
    --screenshot "$output_path" \
    "file://${repo_root}/${html_path}"
}

capture() {
  local html_path="$1"
  local output_name="$2"
  local height="$3"
  local output_path="${output_dir}/${output_name}"

  if command -v chromium >/dev/null 2>&1; then
    capture_with_chromium chromium "$html_path" "$output_path" "$height"
  elif command -v chromium-browser >/dev/null 2>&1; then
    capture_with_chromium chromium-browser "$html_path" "$output_path" "$height"
  elif command -v google-chrome >/dev/null 2>&1; then
    capture_with_chromium google-chrome "$html_path" "$output_path" "$height"
  elif command -v firefox >/dev/null 2>&1; then
    capture_with_firefox "$html_path" "$output_path" "$height"
  else
    echo "No supported headless browser found: install Chromium, Chrome, or Firefox." >&2
    exit 1
  fi
}

capture "examples/qualibact_ecoli/pass_only/report/report.html" "pass_only_report.png" 2200
capture "examples/qualibact_ecoli/fail_only/report/report.html" "fail_only_report.png" 2200
capture "examples/qualibact_ecoli/real_panel/report/report.html" "real_panel_report.png" 2400

echo "Screenshots written to ${output_dir}"
