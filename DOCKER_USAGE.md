# Docker Usage Guide for SpecCheck

## Overview

The SpecCheck Docker image provides a containerized environment for running QC analyses. This guide shows you how to use it effectively.

## Prerequisites

- Docker or OrbStack installed
- Your QC data files ready on your local machine

## Basic Docker Concepts

When running Docker containers, you need to:
1. **Mount volumes** to give the container access to your local files
2. Specify the correct **paths inside the container** (not your local paths)

## Quick Start Examples

### 1. Running the `collect` command

```bash
# Mount your data directory and run collect
docker run --rm \
  -v /path/to/your/data:/data \
  -v /path/to/output:/output \
  happykhan/speccheck:1.1.1 \
  speccheck collect /data/sample_files --sample MySample --output-file /output/results.csv
```

**Explanation:**
- `-v /path/to/your/data:/data` - Mounts your local data directory to `/data` in the container
- `-v /path/to/output:/output` - Mounts your output directory to `/output` in the container
- `--output-file /output/results.csv` - Path **inside the container** where results will be saved
- `--rm` - Automatically removes the container when it exits

### 2. Running the `summary` command

```bash
# Mount directory with CSV files and generate summary
docker run --rm \
  -v /Users/you/project/results:/data \
  -v /Users/you/project/output:/output \
  happykhan/speccheck:1.1.1 \
  speccheck summary /data --output /output
```

**Real example from your setup:**
```bash
docker run --rm \
  -v /Users/nfareed/code/speccheck/kleb_example:/data \
  -v /Users/nfareed/code/speccheck/output:/output \
  happykhan/speccheck:1.1.1 \
  speccheck summary /data --output /output
```

### 3. Running the `check` command

```bash
# Check criteria file integrity
docker run --rm \
  -v /Users/you/criteria.csv:/app/my_criteria.csv \
  happykhan/speccheck:1.1.1 \
  speccheck check --criteria-file /app/my_criteria.csv
```

## Common Patterns

### Using Current Directory

On macOS/Linux, you can use `$(pwd)` to mount the current directory:

```bash
# Run summary on current directory
docker run --rm \
  -v $(pwd):/data \
  -v $(pwd)/output:/output \
  happykhan/speccheck:1.1.1 \
  speccheck summary /data --output /output
```

### Interactive Mode

To explore the container interactively:

```bash
docker run --rm -it \
  -v $(pwd):/data \
  happykhan/speccheck:1.1.1 \
  /bin/bash
```

Then inside the container:
```bash
speccheck --help
ls /data
speccheck summary /data
```

## Important Notes

### ✅ DO:
- Always mount your data directories with `-v`
- Use paths **inside the container** (e.g., `/data`, `/output`) in commands
- Use `--rm` to clean up containers after they exit
- Use absolute paths for volume mounts

### ❌ DON'T:
- Don't use local paths like `/Users/you/data` in speccheck commands
- Don't forget to mount volumes - the container can't see your files otherwise
- Don't use relative paths for volume mounts (they won't work as expected)

## Troubleshooting

### "No data found" error

**Problem:** The container can't see your files.

**Solution:** Make sure you mounted the directory:
```bash
# Wrong - no volume mount
docker run happykhan/speccheck:1.1.1 speccheck summary /Users/you/data

# Right - with volume mount
docker run -v /Users/you/data:/data happykhan/speccheck:1.1.1 speccheck summary /data
```

### Platform warning

You may see:
```
WARNING: The requested image's platform (linux/amd64) does not match the detected host platform (linux/arm64/v8)
```

This is normal on Apple Silicon Macs - the image will still work via Rosetta emulation.

### Permission errors

If you get permission errors writing output files, you may need to set user permissions:

```bash
docker run --rm \
  --user $(id -u):$(id -g) \
  -v $(pwd):/data \
  -v $(pwd)/output:/output \
  happykhan/speccheck:1.1.1 \
  speccheck summary /data --output-dir /output
```

## Complete Working Example

Here's a complete workflow:

```bash
# 1. Create output directory
mkdir -p output

# 2. Collect data for a sample
docker run --rm \
  -v /Users/nfareed/code/speccheck/tests/kleb_test_data:/data \
  -v /Users/nfareed/code/speccheck/output:/output \
  happykhan/speccheck:1.1.1 \
  speccheck collect /data --sample KPN-2072 --output-file /output/KPN-2072.csv

# 3. Generate summary report
docker run --rm \
  -v /Users/nfareed/code/speccheck/kleb_example:/data \
  -v /Users/nfareed/code/speccheck/output:/output \
  happykhan/speccheck:1.1.1 \
  speccheck summary /data --output /output

# 4. View results
open output/report.html
```

## Building Custom Images

If you want to use a custom criteria file:

### Option 1: Mount it at runtime
```bash
docker run --rm \
  -v /path/to/custom_criteria.csv:/app/criteria.csv \
  -v /path/to/data:/data \
  happykhan/speccheck:1.1.1 \
  speccheck collect /data --criteria-file /app/criteria.csv --sample MySample
```

### Option 2: Build a custom image
Create a `Dockerfile`:
```dockerfile
FROM happykhan/speccheck:1.1.1
COPY my_custom_criteria.csv /app/criteria.csv
```

Build it:
```bash
docker build -t myorg/speccheck:custom .
```

## Getting Help

View all available commands and options:
```bash
docker run --rm happykhan/speccheck:1.1.1 speccheck --help
docker run --rm happykhan/speccheck:1.1.1 speccheck collect --help
docker run --rm happykhan/speccheck:1.1.1 speccheck summary --help
docker run --rm happykhan/speccheck:1.1.1 speccheck check --help
```
