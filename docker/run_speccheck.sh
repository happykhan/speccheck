#!/bin/bash
# Helper script to run SpecCheck via Docker with proper volume mounts
# Usage: ./docker/run_speccheck.sh <command> <args...>

set -e

# Configuration
IMAGE="happykhan/speccheck:1.1.1"
DATA_DIR="${DATA_DIR:-$(pwd)}"
OUTPUT_DIR="${OUTPUT_DIR:-$(pwd)/docker_output}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Help message
if [ "$#" -eq 0 ] || [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "SpecCheck Docker Helper Script"
    echo ""
    echo "Usage: $0 <command> [args...]"
    echo ""
    echo "Environment variables:"
    echo "  DATA_DIR     Directory to mount as /data (default: current directory)"
    echo "  OUTPUT_DIR   Directory to mount as /output (default: ./docker_output)"
    echo ""
    echo "Examples:"
    echo "  # Show help"
    echo "  $0 --help"
    echo ""
    echo "  # Run with default directories"
    echo "  $0 summary /data --output /output"
    echo ""
    echo "  # Run with custom data directory"
    echo "  DATA_DIR=/path/to/data $0 summary /data --output /output"
    echo ""
    echo "  # Collect data for a sample"
    echo "  DATA_DIR=./tests/kleb_test_data $0 collect /data --sample KPN-2072 --output-file /output/result.csv"
    echo ""
    echo "  # Interactive mode"
    echo "  $0 bash"
    echo ""
    echo -e "${YELLOW}Note: Use /data for input and /output for output in commands${NC}"
    exit 0
fi

# Check if Docker is available
DOCKER_CMD="docker"
if ! command -v docker &> /dev/null; then
    # Try common locations
    if [ -x "/usr/local/bin/docker" ]; then
        DOCKER_CMD="/usr/local/bin/docker"
        export PATH="/Applications/OrbStack.app/Contents/MacOS/xbin:$PATH"
    elif [ -x "/opt/homebrew/bin/docker" ]; then
        DOCKER_CMD="/opt/homebrew/bin/docker"
    else
        echo -e "${RED}Error: docker command not found${NC}"
        echo "Please install Docker or OrbStack"
        exit 1
    fi
fi

# Determine if we need to prepend 'speccheck'
CMD_PREFIX=""
if [ "$1" != "bash" ] && [ "$1" != "sh" ] && [ "$1" != "/bin/bash" ] && [ "$1" != "/bin/sh" ]; then
    CMD_PREFIX="speccheck"
fi

# Run the container
echo -e "${GREEN}Running SpecCheck Docker container${NC}"
echo -e "Data directory: ${YELLOW}$DATA_DIR${NC} -> /data"
echo -e "Output directory: ${YELLOW}$OUTPUT_DIR${NC} -> /output"
if [ -n "$CMD_PREFIX" ]; then
    echo -e "Command: ${YELLOW}$CMD_PREFIX $@${NC}"
else
    echo -e "Command: ${YELLOW}$@${NC}"
fi
echo ""

if [ -n "$CMD_PREFIX" ]; then
    $DOCKER_CMD run --rm \
        -v "$DATA_DIR":/data \
        -v "$OUTPUT_DIR":/output \
        "$IMAGE" \
        $CMD_PREFIX "$@"
else
    $DOCKER_CMD run --rm -it \
        -v "$DATA_DIR":/data \
        -v "$OUTPUT_DIR":/output \
        "$IMAGE" \
        "$@"
fi

# Show output if any
if [ -n "$(ls -A $OUTPUT_DIR 2>/dev/null)" ]; then
    echo ""
    echo -e "${GREEN}Output files created in: $OUTPUT_DIR${NC}"
    ls -lh "$OUTPUT_DIR"
fi
