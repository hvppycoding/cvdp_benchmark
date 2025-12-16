# CVDP Benchmark Tools

This directory contains utility scripts for working with the CVDP Benchmark.

## Available Tools

### prepare_offline_package.sh
**Purpose**: Prepare a complete offline package for running CVDP Benchmark in environments with limited internet access.

**Usage**:
```bash
chmod +x tools/prepare_offline_package.sh
./tools/prepare_offline_package.sh
```

**What it does**:
- Downloads all Python dependencies (pip packages)
- Downloads dataset files from Hugging Face
- Downloads Icarus Verilog simulator source
- Creates a compressed package ready for offline transfer
- Generates an offline installation guide

**Output**: `cvdp_offline_package.tar.gz` containing everything needed for offline installation.

**Prerequisites**:
- Internet connection (run in online environment)
- `pip`, `wget` or `curl`
- Optional: `huggingface-cli` for automatic dataset download

**See also**: [EXTERNAL_AGENT_GUIDE.md](../EXTERNAL_AGENT_GUIDE.md) - "오프라인 환경 준비 가이드" section

---

### dataset_analyzer.py
**Purpose**: Analyze dataset files and generate statistics.

**Usage**:
```bash
python tools/dataset_analyzer.py -f dataset.jsonl
```

---

### dataset_subset_creator.py
**Purpose**: Create a subset of a dataset based on specific criteria.

**Usage**:
```bash
python tools/dataset_subset_creator.py -f dataset.jsonl -o subset.jsonl [options]
```

---

### jsonl_to_yaml.py
**Purpose**: Convert JSONL dataset files to YAML format for easier reading.

**Usage**:
```bash
python tools/jsonl_to_yaml.py -f dataset.jsonl -o dataset.yaml
```

---

### merge_dataset_files.py
**Purpose**: Merge multiple JSONL dataset files into one.

**Usage**:
```bash
python tools/merge_dataset_files.py -i file1.jsonl file2.jsonl -o merged.jsonl
```

---

### print_testcase.py
**Purpose**: Pretty-print a specific test case from a dataset file.

**Usage**:
```bash
python tools/print_testcase.py -f dataset.jsonl -i test_id
```

---

### refinement_analysis.py
**Purpose**: Analyze refinement iterations and success rates.

**Usage**:
```bash
python tools/refinement_analysis.py -f results.jsonl
```

---

## Contributing

When adding new tools to this directory:
1. Add appropriate documentation header in the script
2. Update this README with usage information
3. Follow existing code style and conventions
