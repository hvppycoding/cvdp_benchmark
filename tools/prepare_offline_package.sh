#!/bin/bash
# prepare_offline_package.sh
# Run in online environment to prepare offline package for CVDP Benchmark
# 
# This script prepares a complete offline package including:
# - CVDP Benchmark repository
# - Python dependencies
# - Dataset files
# - Icarus Verilog simulator source
#
# Usage:
#   chmod +x prepare_offline_package.sh
#   ./prepare_offline_package.sh

set -e

echo "=== CVDP Offline Package Preparation Started ==="
echo ""

# 1. Assume repository is already cloned
REPO_DIR=$(cd "$(dirname "$0")/.." && pwd)
PACKAGE_DIR="${REPO_DIR}_offline_prepared"

echo "Source repository: $REPO_DIR"
echo "Target directory: $PACKAGE_DIR"
echo ""

# Create package directory
mkdir -p "$PACKAGE_DIR"

# 2. Copy repository
echo "[1/6] Copying repository..."
rsync -av --exclude='.git' --exclude='venv*' --exclude='work*' \
  --exclude='__pycache__' --exclude='*.pyc' \
  "$REPO_DIR/" "$PACKAGE_DIR/cvdp_benchmark/"

cd "$PACKAGE_DIR/cvdp_benchmark"

# 3. Download Python packages
echo ""
echo "[2/6] Downloading Python packages..."
mkdir -p offline_packages

if [ -f requirements.txt ]; then
    echo "  - Downloading from requirements.txt..."
    pip download -r requirements.txt -d ./offline_packages
else
    echo "  Warning: requirements.txt not found!"
fi

if [ -f requirements-direct.txt ]; then
    echo "  - Downloading from requirements-direct.txt..."
    pip download -r requirements-direct.txt -d ./offline_packages
else
    echo "  Warning: requirements-direct.txt not found!"
fi

# 4. Download dataset (requires huggingface-cli)
echo ""
echo "[3/6] Downloading dataset..."
if command -v huggingface-cli &> /dev/null; then
    echo "  - Using huggingface-cli to download..."
    huggingface-cli download nvidia/cvdp-benchmark-dataset \
        --repo-type dataset --local-dir ./dataset
    
    # Copy example dataset
    if [ -f dataset/cvdp_v1.0.1_nonagentic_code_generation_no_commercial.jsonl ]; then
        cp dataset/cvdp_v1.0.1_nonagentic_code_generation_no_commercial.jsonl \
            ./dataset.jsonl
        echo "  - Dataset copied to dataset.jsonl"
    else
        echo "  Warning: Example dataset file not found in downloaded data"
    fi
else
    echo "  Warning: huggingface-cli not installed."
    echo "  Please install with: pip install huggingface-hub"
    echo "  Or download manually from: https://huggingface.co/datasets/nvidia/cvdp-benchmark-dataset"
fi

# 5. Download Icarus Verilog source
echo ""
echo "[4/6] Downloading Icarus Verilog..."
mkdir -p offline_tools
cd offline_tools

IVERILOG_VERSION="12_0"
IVERILOG_URL="https://github.com/steveicarus/iverilog/archive/refs/tags/v${IVERILOG_VERSION}.tar.gz"
IVERILOG_FILE="iverilog-${IVERILOG_VERSION}.tar.gz"

if command -v wget &> /dev/null; then
    echo "  - Downloading Icarus Verilog v${IVERILOG_VERSION}..."
    wget -q --show-progress "$IVERILOG_URL" -O "$IVERILOG_FILE"
    echo "  - Downloaded to offline_tools/$IVERILOG_FILE"
elif command -v curl &> /dev/null; then
    echo "  - Downloading Icarus Verilog v${IVERILOG_VERSION} (using curl)..."
    curl -L "$IVERILOG_URL" -o "$IVERILOG_FILE"
    echo "  - Downloaded to offline_tools/$IVERILOG_FILE"
else
    echo "  Warning: Neither wget nor curl found."
    echo "  Please download manually from: $IVERILOG_URL"
fi

cd ..

# 6. Create README
echo ""
echo "[5/6] Creating offline installation guide..."
cat > OFFLINE_INSTALL.md << 'EOF'
# CVDP Benchmark - Offline Installation Guide

This package contains everything needed to run CVDP Benchmark in an offline environment.

## Prerequisites

- Linux/macOS/Windows with WSL
- Python 3.12 or higher
- Build tools (gcc, make) for compiling Icarus Verilog
- USB drive or network transfer method to move files to offline environment

## Installation Steps

### 1. Install Icarus Verilog Simulator

```bash
cd offline_tools
tar -xzf iverilog-12_0.tar.gz
cd iverilog-12_0

# Configure and build
./configure
make

# Install (requires sudo)
sudo make install

# Verify installation
iverilog -V

cd ../..
```

### 2. Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies from offline packages
pip install --no-index --find-links=./offline_packages -r requirements.txt
pip install --no-index --find-links=./offline_packages -r requirements-direct.txt

# Verify installation
python -c "import cocotb; print('cocotb version:', cocotb.__version__)"
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Note: LLM API keys not required for offline evaluation
# You'll use pre-generated answers files instead
```

### 4. Run External Agent Evaluation

See the complete guide in `EXTERNAL_AGENT_GUIDE.md`, specifically:
- "단계별 실행 방법" (Korean) or "Step-by-Step Guide" (English)
- "오프라인 환경 준비 가이드" section for detailed offline setup

### Quick Test

```bash
# Activate virtual environment
source venv/bin/activate

# Run a simple test with golden solutions
python run_direct.py \
  -f example_dataset/cvdp_v1.0.1_example_nonagentic_code_generation_no_commercial_with_solutions.jsonl \
  -i cvdp_copilot_lfsr_0001

# Check results
cat work_direct/report.txt
```

## Troubleshooting

### Icarus Verilog Build Issues

If build fails, ensure you have required tools:
```bash
sudo apt-get install build-essential bison flex gperf
```

### Python Package Installation Issues

If pip cannot find packages:
```bash
# Verify packages are in offline_packages/
ls offline_packages/

# Try installing individual package
pip install --no-index --find-links=./offline_packages <package-name>
```

### Path Issues

Add to your `.bashrc` or `.bash_profile`:
```bash
export PATH=$PATH:/usr/local/bin
export SIM=icarus
```

## Documentation

- `EXTERNAL_AGENT_GUIDE.md` - Complete guide for external agent evaluation
- `README.md` - Main project documentation
- `QUICKSTART_DOCKER_FREE.md` - Quick start without Docker
- `DOCKER_FREE_EXECUTION.md` - Detailed Docker-free execution guide

## Support

For issues or questions:
- GitHub Issues: https://github.com/nvidia-tcad/cvdp_benchmark/issues
- Documentation: See README files in this directory

---

Package created by: tools/prepare_offline_package.sh
EOF

# 7. Compress package
echo ""
echo "[6/6] Compressing package..."
cd "$PACKAGE_DIR"

PACKAGE_FILE="cvdp_offline_package.tar.gz"
tar -czf "$PACKAGE_FILE" cvdp_benchmark/

PACKAGE_SIZE=$(du -h "$PACKAGE_FILE" | cut -f1)

echo ""
echo "=== Preparation Complete! ==="
echo ""
echo "Created package:"
echo "  File: $PACKAGE_DIR/$PACKAGE_FILE"
echo "  Size: $PACKAGE_SIZE"
echo ""
echo "Next steps:"
echo "  1. Transfer $PACKAGE_FILE to your offline environment"
echo "  2. Extract: tar -xzf $PACKAGE_FILE"
echo "  3. Follow OFFLINE_INSTALL.md for installation instructions"
echo ""
echo "Happy offline benchmarking!"
