# Docker 없이 빠르게 시작하기 (Quick Start Without Docker)

## 한국어 빠른 시작 가이드

### 1단계: 환경 준비

```bash
# Python 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 필수 패키지 설치
pip install -r requirements.txt

# Verilog 시뮬레이터 설치 (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install iverilog
```

### 2단계: 테스트 실행

```bash
# 단일 테스트 케이스 실행
python run_direct.py -f example_dataset/cvdp_v1.0.1_example_nonagentic_code_generation_no_commercial_with_solutions.jsonl -i cvdp_copilot_lfsr_0001

# 전체 예제 데이터셋 실행
python run_direct.py -f example_dataset/cvdp_v1.0.1_example_nonagentic_code_generation_no_commercial_with_solutions.jsonl

# 결과 확인
cat work_direct/report.txt
```

### 3단계: 결과 분석

```
work_direct/
├── report.txt              # 전체 테스트 결과 요약
└── cvdp_copilot_lfsr_0001/ # 각 테스트 케이스별 디렉토리
    ├── rtl/                # RTL 소스 파일
    ├── src/                # 테스트 파일
    ├── rundir/             # 실행 결과
    └── test_output.log     # 상세 로그
```

## 간단한 예제 실행

```bash
# 교육용 예제 스크립트 실행
python examples/extract_and_run_simple.py

# 생성된 파일 확인
ls -R example_manual_run/

# 수동으로 테스트 실행하기
cd example_manual_run/cvdp_copilot_lfsr_0001/rundir
export SIM=icarus
export VERILOG_SOURCES=$(cd .. && pwd)/rtl/*.sv
export TOPLEVEL=lfsr_8bit
export MODULE=test_lfsr
export PYTHONPATH=$(cd ../src && pwd)
pytest -s ../src/test_runner.py -v
```

## 자주 묻는 질문 (FAQ)

### Q: Docker가 꼭 필요한가요?
A: 아니요. 이 가이드의 방법을 사용하면 Docker 없이 테스트를 실행할 수 있습니다.

### Q: 어떤 시뮬레이터가 필요한가요?
A: Icarus Verilog (오픈소스) 또는 Verilator를 사용할 수 있습니다. Icarus Verilog를 권장합니다.

### Q: 상용 EDA 도구가 필요한 테스트도 실행할 수 있나요?
A: 아니요. 상용 도구(Cadence Xcelium 등)가 필요한 테스트는 Docker 환경이 필요합니다.

### Q: dataset.jsonl 파일은 어디서 구하나요?
A: [Hugging Face](https://huggingface.co/datasets/nvidia/cvdp-benchmark-dataset)에서 다운로드하거나 `example_dataset/` 디렉토리의 예제를 사용하세요.

### Q: 테스트가 실패하면 어떻게 하나요?
A: `work_direct/[테스트ID]/test_output.log` 파일을 확인하여 상세한 오류 메시지를 볼 수 있습니다.

## 상세 문서

더 자세한 내용은 다음 문서를 참고하세요:
- [DOCKER_FREE_EXECUTION.md](DOCKER_FREE_EXECUTION.md) - 전체 가이드 (한국어/영어)
- [README.md](README.md) - 프로젝트 개요
- [README_NON_AGENTIC.md](README_NON_AGENTIC.md) - 비에이전트 워크플로우 가이드

---

# English Quick Start Guide

## Prerequisites

```bash
# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install -r requirements.txt

# Install Verilog simulator (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install iverilog
```

## Running Tests

```bash
# Run single test case
python run_direct.py -f example_dataset/cvdp_v1.0.1_example_nonagentic_code_generation_no_commercial_with_solutions.jsonl -i cvdp_copilot_lfsr_0001

# Run all example tests
python run_direct.py -f example_dataset/cvdp_v1.0.1_example_nonagentic_code_generation_no_commercial_with_solutions.jsonl

# View results
cat work_direct/report.txt
```

## Output Structure

```
work_direct/
├── report.txt              # Overall test summary
└── cvdp_copilot_lfsr_0001/ # Per-test directories
    ├── rtl/                # RTL source files
    ├── src/                # Test files
    ├── rundir/             # Execution results
    └── test_output.log     # Detailed logs
```

## Simple Example

```bash
# Run educational example
python examples/extract_and_run_simple.py

# Check extracted files
ls -R example_manual_run/

# Manual test execution
cd example_manual_run/cvdp_copilot_lfsr_0001/rundir
export SIM=icarus
export VERILOG_SOURCES=$(cd .. && pwd)/rtl/*.sv
export TOPLEVEL=lfsr_8bit
export MODULE=test_lfsr
export PYTHONPATH=$(cd ../src && pwd)
pytest -s ../src/test_runner.py -v
```

## FAQ

### Q: Is Docker required?
A: No. You can run tests without Docker using the methods in this guide.

### Q: Which simulator is needed?
A: Icarus Verilog (open source) or Verilator. We recommend Icarus Verilog.

### Q: Can I run tests requiring commercial EDA tools?
A: No. Tests requiring commercial tools (Cadence Xcelium, etc.) need Docker environment.

### Q: Where do I get dataset.jsonl files?
A: Download from [Hugging Face](https://huggingface.co/datasets/nvidia/cvdp-benchmark-dataset) or use examples in `example_dataset/`.

### Q: What if a test fails?
A: Check `work_direct/[test_id]/test_output.log` for detailed error messages.

## Detailed Documentation

For more information, see:
- [DOCKER_FREE_EXECUTION.md](DOCKER_FREE_EXECUTION.md) - Complete guide (Korean/English)
- [README.md](README.md) - Project overview
- [README_NON_AGENTIC.md](README_NON_AGENTIC.md) - Non-agentic workflow guide
