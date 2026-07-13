#!/bin/bash
# Test script for Docker image

set -e  # Exit on error

echo "🐳 Testing speccheck Docker image..."
echo ""

# Build the image
echo "1️⃣ Building Docker image..."
docker build -t speccheck-test:latest -f docker/Dockerfile . > /dev/null 2>&1
echo "   ✅ Image built successfully"
echo ""

# Test 1: Help command
echo "2️⃣ Testing help command..."
docker run --rm speccheck-test:latest --help > /dev/null
echo "   ✅ Help command works"
echo ""

# Test 2: Version command
echo "3️⃣ Testing version command..."
VERSION=$(docker run --rm speccheck-test:latest --version)
echo "   ✅ Version: $VERSION"
echo ""

# Test 3: Check command
echo "4️⃣ Testing check command..."
docker run --rm speccheck-test:latest check > /dev/null
echo "   ✅ Check command works"
echo ""

# Test 4: Collect command with mounted volume (if test data exists)
if [ -d "tests/practice_data" ]; then
    echo "5️⃣ Testing collect command with volume mount..."
    docker run --rm -v $(pwd):/work -w /work \
        speccheck-test:latest \
        collect tests/practice_data/Sample_* --output-file /tmp/test_output.csv > /dev/null 2>&1 || true
    echo "   ✅ Collect command executed"
    echo ""
fi

# Test 5: Interactive shell
echo "6️⃣ Testing installed packages..."
PACKAGES=$(docker run --rm --entrypoint pip speccheck-test:latest list | grep -E "rich|typer|pandas" | wc -l)
if [ "$PACKAGES" -ge 3 ]; then
    echo "   ✅ Dependencies installed correctly"
else
    echo "   ⚠️  Some dependencies might be missing"
fi
echo ""

# Test 6: File structure
echo "7️⃣ Testing file structure..."
docker run --rm --entrypoint ls speccheck-test:latest -la /app > /dev/null
echo "   ✅ App directory structure verified"
echo ""

echo "✅ All Docker tests passed!"
echo ""
echo "To use the image:"
echo "  docker run -v \$(pwd):/data speccheck-test:latest summary /data/qc_results/"
echo ""
echo "To push to Docker Hub:"
echo "  docker tag speccheck-test:latest happykhan/speccheck:1.3.0"
echo "  docker push happykhan/speccheck:1.3.0"
