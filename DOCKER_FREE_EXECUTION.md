# Docker 없이 dataset.jsonl로 테스트 실행하기
# Running Tests with dataset.jsonl Without Docker

[English version below]

## 한국어 (Korean)

### 개요

이 문서는 CVDP Benchmark를 Docker 없이 dataset.jsonl 파일만으로 실행하는 방법을 설명합니다.

### 현재 아키텍처 분석

#### Docker 기반 실행 흐름
1. **데이터 추출**: dataset.jsonl에서 테스트 케이스 읽기
2. **파일 생성**: harness, rtl, verif 디렉토리와 파일 생성
3. **Docker 빌드**: docker-compose.yml을 사용하여 테스트 환경 구축
4. **Docker 실행**: 컨테이너 내에서 cocotb + pytest 실행
5. **결과 수집**: 테스트 결과를 호스트로 반환

#### Docker가 사용되는 위치
- `src/repository.py`의 `obj_harness()` 메소드
- `log_docker()` 메소드가 docker-compose 명령 실행
- 각 테스트는 독립된 Docker 컨테이너에서 실행

### Docker 없이 실행하는 방법

#### 방법 1: 직접 실행 (권장)

현재 코드베이스는 이미 Docker 없이 실행할 수 있는 기능을 부분적으로 지원합니다:

**필수 요구사항:**
```bash
# Python 3.12 권장
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Verilog 시뮬레이터 설치 (하나 선택)
# - Icarus Verilog (오픈소스)
sudo apt-get install iverilog
# 또는
# - Verilator (오픈소스)
sudo apt-get install verilator
```

**단계별 실행:**

1. **테스트 파일 추출**
```python
import json

# dataset.jsonl 읽기
with open('example_dataset/cvdp_v1.0.1_example_nonagentic_code_generation_no_commercial_with_solutions.jsonl', 'r') as f:
    data = json.loads(f.readline())

# 테스트 케이스 ID
test_id = data['id']
print(f"Test ID: {test_id}")

# 파일 저장 위치
import os
base_dir = f"work_direct/{test_id}"
os.makedirs(base_dir, exist_ok=True)

# RTL 파일 저장
if 'output' in data and 'context' in data['output']:
    for filepath, content in data['output']['context'].items():
        full_path = os.path.join(base_dir, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)

# 테스트 하네스 파일 저장
if 'harness' in data and 'files' in data['harness']:
    for filepath, content in data['harness']['files'].items():
        if filepath.startswith('src/'):
            full_path = os.path.join(base_dir, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
```

2. **환경 변수 설정**
```bash
cd work_direct/cvdp_copilot_lfsr_0001
export SIM=icarus
export TOPLEVEL_LANG=verilog
export VERILOG_SOURCES=$(pwd)/rtl/lfsr_8bit.sv
export TOPLEVEL=lfsr_8bit
export MODULE=test_lfsr
```

3. **테스트 실행**
```bash
# pytest로 테스트 실행
pytest -s src/test_runner.py -v
```

#### 방법 2: 제공된 스크립트 사용

새로 추가된 `run_direct.py` 스크립트를 사용하면 더 간단합니다:

```bash
# 단일 테스트 케이스 실행
python run_direct.py -f example_dataset/cvdp_v1.0.1_example_nonagentic_code_generation_no_commercial_with_solutions.jsonl -i cvdp_copilot_lfsr_0001

# 전체 데이터셋 실행
python run_direct.py -f example_dataset/cvdp_v1.0.1_example_nonagentic_code_generation_no_commercial_with_solutions.jsonl

# 결과 확인
cat work_direct/report.txt
```

### 제한사항

1. **시뮬레이터 필요**: Icarus Verilog 또는 Verilator가 시스템에 설치되어 있어야 함
2. **상용 EDA 도구**: 상용 도구가 필요한 테스트는 Docker 없이 실행 불가
3. **환경 격리**: Docker 없이는 테스트 간 환경 격리가 제한적
4. **재현성**: Docker 환경보다 재현성이 낮을 수 있음

### 장점

1. **빠른 실행**: Docker 오버헤드 없음
2. **간단한 디버깅**: 호스트 시스템에서 직접 디버깅 가능
3. **가벼운 환경**: Docker 설치 불필요

---

## English

### Overview

This document explains how to run CVDP Benchmark with just a dataset.jsonl file without Docker.

### Current Architecture Analysis

#### Docker-Based Execution Flow
1. **Data Extraction**: Read test cases from dataset.jsonl
2. **File Creation**: Generate harness, rtl, verif directories and files
3. **Docker Build**: Build test environment using docker-compose.yml
4. **Docker Execution**: Run cocotb + pytest inside containers
5. **Result Collection**: Return test results to host

#### Where Docker is Used
- `obj_harness()` method in `src/repository.py`
- `log_docker()` method executes docker-compose commands
- Each test runs in an isolated Docker container

### How to Run Without Docker

#### Method 1: Direct Execution (Recommended)

The current codebase already partially supports running without Docker:

**Prerequisites:**
```bash
# Python 3.12 recommended
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Verilog simulator (choose one)
# - Icarus Verilog (open source)
sudo apt-get install iverilog
# or
# - Verilator (open source)
sudo apt-get install verilator
```

**Step-by-Step Execution:**

1. **Extract Test Files**
```python
import json

# Read dataset.jsonl
with open('example_dataset/cvdp_v1.0.1_example_nonagentic_code_generation_no_commercial_with_solutions.jsonl', 'r') as f:
    data = json.loads(f.readline())

# Test case ID
test_id = data['id']
print(f"Test ID: {test_id}")

# File save location
import os
base_dir = f"work_direct/{test_id}"
os.makedirs(base_dir, exist_ok=True)

# Save RTL files
if 'output' in data and 'context' in data['output']:
    for filepath, content in data['output']['context'].items():
        full_path = os.path.join(base_dir, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)

# Save test harness files
if 'harness' in data and 'files' in data['harness']:
    for filepath, content in data['harness']['files'].items():
        if filepath.startswith('src/'):
            full_path = os.path.join(base_dir, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
```

2. **Set Environment Variables**
```bash
cd work_direct/cvdp_copilot_lfsr_0001
export SIM=icarus
export TOPLEVEL_LANG=verilog
export VERILOG_SOURCES=$(pwd)/rtl/lfsr_8bit.sv
export TOPLEVEL=lfsr_8bit
export MODULE=test_lfsr
```

3. **Run Tests**
```bash
# Run tests with pytest
pytest -s src/test_runner.py -v
```

#### Method 2: Use Provided Script

Using the newly added `run_direct.py` script is simpler:

```bash
# Run single test case
python run_direct.py -f example_dataset/cvdp_v1.0.1_example_nonagentic_code_generation_no_commercial_with_solutions.jsonl -i cvdp_copilot_lfsr_0001

# Run entire dataset
python run_direct.py -f example_dataset/cvdp_v1.0.1_example_nonagentic_code_generation_no_commercial_with_solutions.jsonl

# Check results
cat work_direct/report.txt
```

### Limitations

1. **Simulator Required**: Icarus Verilog or Verilator must be installed on the system
2. **Commercial EDA Tools**: Tests requiring commercial tools cannot run without Docker
3. **Environment Isolation**: Limited isolation between tests without Docker
4. **Reproducibility**: May have lower reproducibility than Docker environment

### Advantages

1. **Faster Execution**: No Docker overhead
2. **Simple Debugging**: Direct debugging on host system
3. **Lightweight**: No Docker installation required

### Dataset Structure

Each entry in dataset.jsonl contains:
- `id`: Test case identifier
- `input`: Problem prompt and context
- `output`: Expected RTL/solution files
- `harness`: Test infrastructure (test files, docker-compose, etc.)

### Technical Details

**Key Components:**
- **cocotb**: Python-based HDL verification framework
- **pytest**: Test execution framework
- **Icarus Verilog / Verilator**: Open-source Verilog simulators

**Execution Environment:**
- Python environment with cocotb and pytest installed
- Verilog simulator accessible in PATH
- Environment variables set for cocotb configuration
