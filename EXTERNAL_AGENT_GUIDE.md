# 외부 Agent를 사용한 평가 가이드
# External Agent Evaluation Guide

[English version below]

## 한국어 (Korean)

### 개요

이 가이드는 **외부 Agent 어플리케이션**을 사용하여 CVDP 벤치마크를 평가하는 방법을 설명합니다. LLM API를 함수로 호출하는 대신, 독립적인 Agent 프로그램을 사용하고 평가만 수행할 수 있습니다.

### 워크플로우

```
1. 환경 셋업 (dataset.jsonl에서 파일 추출)
   ↓
2. 외부 Agent에게 프롬프트 전달 및 실행
   ↓
3. Agent 결과물을 answers 파일로 저장
   ↓
4. 평가만 실행 (CVDP 프레임워크 사용)
```

---

## 오프라인 환경 준비 가이드 (Offline Environment Setup)

### 개요

오프라인 환경(인터넷 연결이 제한적이지만 pip, npm은 사용 가능)에서 External Agent를 사용하려면, 필요한 모든 파일을 미리 준비하여 오프라인 환경으로 옮겨야 합니다.

### 1단계: 온라인 환경에서 파일 준비

#### 1.1 저장소 클론 및 데이터셋 다운로드

```bash
# CVDP 벤치마크 저장소 클론
git clone https://github.com/nvidia-tcad/cvdp_benchmark.git
cd cvdp_benchmark

# dataset.jsonl 다운로드 (Hugging Face에서)
# 방법 1: 웹 브라우저로 다운로드
# https://huggingface.co/datasets/nvidia/cvdp-benchmark-dataset

# 방법 2: huggingface-cli 사용
pip install huggingface-hub
huggingface-cli download nvidia/cvdp-benchmark-dataset --repo-type dataset --local-dir ./dataset

# 필요한 dataset.jsonl 파일을 프로젝트 루트로 복사
cp dataset/cvdp_v1.0.1_nonagentic_code_generation_no_commercial.jsonl ./dataset.jsonl
```

#### 1.2 Python 의존성 다운로드

```bash
# 가상환경 생성 (권장)
python3 -m venv venv_online
source venv_online/bin/activate  # Windows: venv_online\Scripts\activate

# pip 업그레이드
pip install --upgrade pip

# 의존성 다운로드 (설치하지 않고 다운로드만)
pip download -r requirements.txt -d ./offline_packages

# Docker-free 실행을 위한 추가 패키지 다운로드
pip download -r requirements-direct.txt -d ./offline_packages

# 중복 제거 및 정리
# (선택사항: 필요시 수동으로 중복 파일 제거)
```

#### 1.3 시뮬레이터 및 도구 준비

**Icarus Verilog (권장):**

```bash
# Ubuntu/Debian 패키지 다운로드
mkdir -p offline_tools
cd offline_tools

# Icarus Verilog 패키지 다운로드
apt-get download iverilog
# 의존성 패키지도 함께 다운로드
apt-cache depends iverilog | grep Depends | awk '{print $2}' | xargs apt-get download

cd ..
```

**또는 소스에서 빌드용 tarball 다운로드:**

```bash
mkdir -p offline_tools
cd offline_tools

# Icarus Verilog 소스 다운로드
wget https://github.com/steveicarus/iverilog/archive/refs/tags/v12_0.tar.gz -O iverilog-12.0.tar.gz

cd ..
```

**NPM 패키지 (External Agent가 Node.js를 사용하는 경우):**

```bash
# Node.js 기반 External Agent를 사용하는 경우
# 프로젝트에 package.json이 있다면

mkdir -p offline_npm_packages
cd your_agent_directory

# package-lock.json 생성 (없는 경우)
npm install

# 오프라인 tarball 생성
npm pack

# 또는 npm 캐시를 통한 오프라인 패키지 준비
npm install --prefer-offline
# npm 캐시 디렉토리 복사 (~/.npm 또는 %AppData%/npm-cache)
mkdir -p ../offline_npm_packages
cp -r ~/.npm ../offline_npm_packages/npm-cache

cd ..
```

#### 1.4 전체 패키지 압축

```bash
# 오프라인 전송을 위한 전체 패키지 생성
cd ..
tar -czf cvdp_offline_package.tar.gz cvdp_benchmark/
```

### 2단계: 오프라인 환경으로 파일 전송

```bash
# USB, 네트워크 드라이브 등을 통해 전송
# cvdp_offline_package.tar.gz를 오프라인 환경으로 복사
```

### 3단계: 오프라인 환경에서 설치

#### 3.1 패키지 압축 해제

```bash
# 오프라인 환경에서
tar -xzf cvdp_offline_package.tar.gz
cd cvdp_benchmark
```

#### 3.2 시뮬레이터 설치

**방법 1: 다운로드한 .deb 패키지 설치 (Ubuntu/Debian):**

```bash
cd offline_tools
sudo dpkg -i *.deb
# 의존성 문제 해결 (필요시)
sudo apt-get install -f

cd ..
```

**방법 2: 소스에서 빌드:**

```bash
cd offline_tools
tar -xzf iverilog-12.0.tar.gz
cd iverilog-12_0
./configure
make
sudo make install

cd ../..
```

#### 3.3 Python 환경 설정

```bash
# 가상환경 생성
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 오프라인 패키지에서 의존성 설치
pip install --no-index --find-links=./offline_packages -r requirements.txt
pip install --no-index --find-links=./offline_packages -r requirements-direct.txt
```

**NPM 패키지 설치 (Node.js 기반 Agent 사용 시):**

```bash
# 방법 1: npm 캐시 사용
cp -r offline_npm_packages/npm-cache ~/.npm

cd your_agent_directory
npm install --offline

# 방법 2: 로컬 tarball 사용
cd your_agent_directory
npm install /path/to/your-agent-package.tgz

cd ..
```

#### 3.4 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (필요시)
# 오프라인 환경에서는 LLM API 키 불필요 (answers 파일 사용)
```

### 4단계: 오프라인 환경에서 External Agent 실행

오프라인 환경이 준비되면 아래의 "단계별 실행 방법"을 따라 진행하세요.

**주요 참고사항:**
- LLM API 호출은 사용하지 않으므로 인터넷 연결 불필요
- External Agent의 실행 결과를 answers 파일로 저장
- 평가만 로컬에서 실행 (`-a` 옵션 사용)

### 체크리스트: 오프라인 환경 준비 완료 확인

- [ ] CVDP 벤치마크 저장소 복사 완료
- [ ] dataset.jsonl 파일 준비 완료
- [ ] Python 의존성 패키지 (offline_packages) 준비 완료
- [ ] Icarus Verilog 또는 Verilator 설치 완료
- [ ] Python 가상환경 생성 및 패키지 설치 완료
- [ ] External Agent 프로그램 준비 완료 (있는 경우)

### 문제 해결 (Offline Troubleshooting)

**문제: pip 설치 시 "Could not find a version" 오류**
```bash
# 해결: wheel 파일이 offline_packages에 있는지 확인
ls offline_packages/

# 누락된 패키지가 있다면, 온라인 환경에서 다시 다운로드
# pip download <package-name> -d ./offline_packages
```

**문제: Icarus Verilog 실행 시 "command not found"**
```bash
# 해결: PATH 확인
which iverilog

# 수동으로 PATH 추가 (필요시)
export PATH=$PATH:/usr/local/bin
```

**문제: cocotb 실행 시 시뮬레이터를 찾지 못함**
```bash
# 해결: SIM 환경 변수 확인
export SIM=icarus

# 시뮬레이터가 PATH에 있는지 확인
which iverilog
```

**문제: npm install 시 네트워크 오류**
```bash
# 해결: --offline 또는 --prefer-offline 플래그 사용
npm install --offline

# 또는 npm 레지스트리를 로컬로 설정
npm config set registry http://localhost:4873
```

### 자동화 스크립트 예시: 오프라인 패키지 준비

온라인 환경에서 실행하여 모든 필요한 파일을 한 번에 준비하는 스크립트:

```bash
#!/bin/bash
# prepare_offline_package.sh
# 온라인 환경에서 실행하여 오프라인 패키지를 준비하는 스크립트

set -e

echo "=== CVDP 오프라인 패키지 준비 시작 ==="

# 1. 저장소가 이미 클론되어 있다고 가정
REPO_DIR=$(pwd)
PACKAGE_DIR="${REPO_DIR}_offline_prepared"

echo "작업 디렉토리: $PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

# 2. 저장소 복사
echo "[1/6] 저장소 복사..."
rsync -av --exclude='.git' --exclude='venv*' --exclude='work*' \
  "$REPO_DIR/" "$PACKAGE_DIR/cvdp_benchmark/"

cd "$PACKAGE_DIR/cvdp_benchmark"

# 3. Python 패키지 다운로드
echo "[2/6] Python 패키지 다운로드..."
mkdir -p offline_packages
pip download -r requirements.txt -d ./offline_packages
pip download -r requirements-direct.txt -d ./offline_packages

# 4. 데이터셋 다운로드 (huggingface-cli 필요)
echo "[3/6] 데이터셋 다운로드..."
if command -v huggingface-cli &> /dev/null; then
    huggingface-cli download nvidia/cvdp-benchmark-dataset \
        --repo-type dataset --local-dir ./dataset
    cp dataset/cvdp_v1.0.1_nonagentic_code_generation_no_commercial.jsonl \
        ./dataset.jsonl
else
    echo "경고: huggingface-cli가 설치되지 않았습니다."
    echo "수동으로 https://huggingface.co/datasets/nvidia/cvdp-benchmark-dataset 에서 다운로드하세요."
fi

# 5. Icarus Verilog 소스 다운로드
echo "[4/6] Icarus Verilog 다운로드..."
mkdir -p offline_tools
cd offline_tools
if command -v wget &> /dev/null; then
    wget https://github.com/steveicarus/iverilog/archive/refs/tags/v12_0.tar.gz \
        -O iverilog-12.0.tar.gz
else
    echo "경고: wget이 설치되지 않았습니다."
    echo "수동으로 Icarus Verilog를 다운로드하세요."
fi
cd ..

# 6. README 파일 생성
echo "[5/6] 오프라인 설치 가이드 생성..."
cat > OFFLINE_INSTALL.md << 'EOF'
# 오프라인 설치 가이드

## 1. 시뮬레이터 설치
```bash
cd offline_tools
tar -xzf iverilog-12.0.tar.gz
cd iverilog-12_0
./configure
make
sudo make install
cd ../..
```

## 2. Python 환경 설정
```bash
python3 -m venv venv
source venv/bin/activate
pip install --no-index --find-links=./offline_packages -r requirements.txt
pip install --no-index --find-links=./offline_packages -r requirements-direct.txt
```

## 3. 실행
EXTERNAL_AGENT_GUIDE.md 문서의 "단계별 실행 방법"을 참조하세요.
EOF

# 7. 압축
echo "[6/6] 패키지 압축..."
cd "$PACKAGE_DIR"
tar -czf cvdp_offline_package.tar.gz cvdp_benchmark/

echo ""
echo "=== 완료! ==="
echo "생성된 파일: $PACKAGE_DIR/cvdp_offline_package.tar.gz"
echo "이 파일을 오프라인 환경으로 전송하세요."
```

사용 방법:
```bash
chmod +x prepare_offline_package.sh
./prepare_offline_package.sh
```

---

### 단계별 실행 방법

#### 1단계: 환경 셋업 (파일 추출)

먼저 dataset.jsonl에서 필요한 파일들을 추출합니다:

```python
import json
import os

# dataset.jsonl 읽기
with open('dataset.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)
        test_id = data['id']
        
        # 작업 디렉토리 생성
        work_dir = f"external_agent_workspace/{test_id}"
        os.makedirs(work_dir, exist_ok=True)
        
        # 프롬프트 저장
        prompt = data['input']['prompt']
        with open(f"{work_dir}/prompt.txt", 'w') as pf:
            pf.write(prompt)
        
        # 컨텍스트 파일 저장 (있는 경우)
        if 'context' in data['input']:
            for filename, content in data['input']['context'].items():
                filepath = os.path.join(work_dir, filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'w') as cf:
                    cf.write(content)
        
        print(f"Prepared workspace for {test_id}")
```

#### 2단계: 외부 Agent 실행

이제 각 테스트 케이스에 대해 외부 Agent를 실행합니다:

```bash
# 예시: 각 테스트 케이스에 대해 Agent 실행
for test_dir in external_agent_workspace/*/; do
    test_id=$(basename "$test_dir")
    
    # Agent에 프롬프트 전달 및 실행
    # (여기서는 예시로 가상의 my-agent 명령어 사용)
    my-agent \
        --prompt "$test_dir/prompt.txt" \
        --workspace "$test_dir" \
        --output "$test_dir/solution.v"
    
    echo "Completed $test_id"
done
```

또는 Python으로:

```python
import subprocess

workspace_dir = "external_agent_workspace"
for test_id in os.listdir(workspace_dir):
    test_path = os.path.join(workspace_dir, test_id)
    
    # 프롬프트 읽기
    with open(f"{test_path}/prompt.txt", 'r') as f:
        prompt = f.read()
    
    # 외부 Agent 실행
    result = subprocess.run([
        'my-agent',
        '--prompt', prompt,
        '--workspace', test_path,
        '--output', f'{test_path}/solution.v'
    ])
    
    print(f"Agent completed {test_id} with code {result.returncode}")
```

#### 3단계: Answers 파일 생성

Agent의 출력을 CVDP가 인식할 수 있는 answers 형식으로 변환합니다:

```python
import json

answers = []

# 원본 dataset 읽기
with open('dataset.jsonl', 'r') as f:
    dataset = [json.loads(line) for line in f]

# 각 테스트 케이스의 결과를 answers 형식으로 변환
for data in dataset:
    test_id = data['id']
    work_dir = f"external_agent_workspace/{test_id}"
    
    # Agent가 생성한 솔루션 읽기
    solution_files = {}
    
    # 예시: RTL 파일 읽기
    solution_path = f"{work_dir}/solution.v"
    if os.path.exists(solution_path):
        with open(solution_path, 'r') as sf:
            # dataset에서 예상되는 출력 파일 경로 확인
            if 'output' in data and 'context' in data['output']:
                # 첫 번째 출력 파일의 경로를 사용
                output_key = list(data['output']['context'].keys())[0]
                solution_files[output_key] = sf.read()
    
    # Answers 형식: {test_id: {input: ..., output: {context: ...}}}
    answer_entry = {
        test_id: {
            'input': data['input'],
            'output': {
                'response': '',  # 선택사항
                'context': solution_files
            }
        }
    }
    
    answers.append(answer_entry)

# Answers 파일 저장 (JSONL 형식)
with open('my_agent_answers.jsonl', 'w') as f:
    for answer in answers:
        f.write(json.dumps(answer) + '\n')

print(f"Created answers file with {len(answers)} entries")
```

#### 4단계: 평가만 실행

이제 Agent의 결과물을 평가합니다:

```bash
# 평가만 실행 (LLM 호출 없이)
python run_benchmark.py \
    -f dataset.jsonl \
    -a my_agent_answers.jsonl \
    -p work_external_agent

# 결과 확인
cat work_external_agent/report.txt
```

### Answers 파일 형식

Answers 파일은 JSONL 형식이며, 각 줄은 다음과 같은 구조를 가집니다:

```json
{
  "cvdp_copilot_test_0001": {
    "input": {
      "prompt": "원본 프롬프트...",
      "context": {}
    },
    "output": {
      "response": "",
      "context": {
        "rtl/module.v": "Agent가 생성한 Verilog 코드..."
      }
    }
  }
}
```

**중요:**
- 각 줄은 하나의 테스트 케이스 결과를 포함
- Key는 테스트 케이스 ID
- `output.context`에 Agent가 생성한 파일들을 포함
- 파일 경로는 원본 dataset의 `output.context` 키와 일치해야 함

### 전체 자동화 스크립트 예시

```python
#!/usr/bin/env python3
"""
외부 Agent를 사용한 CVDP 벤치마크 평가 자동화 스크립트
"""

import json
import os
import subprocess
import sys

def setup_workspace(dataset_file, workspace_dir):
    """1단계: 작업 공간 설정"""
    os.makedirs(workspace_dir, exist_ok=True)
    
    with open(dataset_file, 'r') as f:
        dataset = [json.loads(line) for line in f]
    
    for data in dataset:
        test_id = data['id']
        test_dir = os.path.join(workspace_dir, test_id)
        os.makedirs(test_dir, exist_ok=True)
        
        # 프롬프트 저장
        with open(f"{test_dir}/prompt.txt", 'w') as pf:
            pf.write(data['input']['prompt'])
        
        print(f"Setup workspace for {test_id}")
    
    return dataset

def run_external_agent(workspace_dir, agent_command):
    """2단계: 외부 Agent 실행"""
    for test_id in os.listdir(workspace_dir):
        test_dir = os.path.join(workspace_dir, test_id)
        
        # Agent 실행
        cmd = agent_command.format(
            test_id=test_id,
            test_dir=test_dir,
            prompt=f"{test_dir}/prompt.txt"
        )
        
        print(f"Running agent for {test_id}...")
        result = subprocess.run(cmd, shell=True)
        
        if result.returncode != 0:
            print(f"Warning: Agent failed for {test_id}")

def create_answers_file(dataset, workspace_dir, output_file):
    """3단계: Answers 파일 생성"""
    answers = []
    
    for data in dataset:
        test_id = data['id']
        test_dir = os.path.join(workspace_dir, test_id)
        
        # Agent 출력 수집
        solution_files = {}
        
        # dataset의 예상 출력 파일들을 확인
        if 'output' in data and 'context' in data['output']:
            for expected_path in data['output']['context'].keys():
                # Agent가 생성한 파일 찾기
                agent_output = os.path.join(test_dir, os.path.basename(expected_path))
                if os.path.exists(agent_output):
                    with open(agent_output, 'r') as f:
                        solution_files[expected_path] = f.read()
        
        # Answers 엔트리 생성
        answer_entry = {
            test_id: {
                'input': data['input'],
                'output': {
                    'response': '',
                    'context': solution_files
                }
            }
        }
        
        answers.append(answer_entry)
    
    # JSONL 형식으로 저장
    with open(output_file, 'w') as f:
        for answer in answers:
            f.write(json.dumps(answer) + '\n')
    
    print(f"Created answers file: {output_file}")

def run_evaluation(dataset_file, answers_file, output_dir):
    """4단계: 평가 실행"""
    cmd = [
        'python', 'run_benchmark.py',
        '-f', dataset_file,
        '-a', answers_file,
        '-p', output_dir
    ]
    
    print(f"Running evaluation...")
    subprocess.run(cmd)
    print(f"Evaluation complete. Results in {output_dir}/report.txt")

def main():
    # 설정
    dataset_file = 'dataset.jsonl'
    workspace_dir = 'external_agent_workspace'
    answers_file = 'my_agent_answers.jsonl'
    output_dir = 'work_external_agent'
    
    # Agent 명령어 템플릿
    # {test_id}, {test_dir}, {prompt}를 사용할 수 있음
    agent_command = 'my-agent --prompt {prompt} --output {test_dir}/solution.v'
    
    # 실행
    print("=== Step 1: Setup Workspace ===")
    dataset = setup_workspace(dataset_file, workspace_dir)
    
    print("\n=== Step 2: Run External Agent ===")
    run_external_agent(workspace_dir, agent_command)
    
    print("\n=== Step 3: Create Answers File ===")
    create_answers_file(dataset, workspace_dir, answers_file)
    
    print("\n=== Step 4: Run Evaluation ===")
    run_evaluation(dataset_file, answers_file, output_dir)
    
    print("\n=== Complete! ===")

if __name__ == '__main__':
    main()
```

사용 방법:
```bash
# 스크립트 수정 (agent_command 부분을 실제 Agent 명령어로)
# 실행
python evaluate_external_agent.py
```

### 팁과 모범 사례

1. **파일 경로 일치**: Agent 출력 파일 경로가 dataset의 `output.context` 키와 정확히 일치해야 합니다.

2. **병렬 처리**: 여러 테스트 케이스를 동시에 처리하려면:
   ```python
   from concurrent.futures import ThreadPoolExecutor
   
   with ThreadPoolExecutor(max_workers=4) as executor:
       executor.map(run_agent_for_test, test_ids)
   ```

3. **에러 처리**: Agent 실패 시 부분 결과도 평가할 수 있도록:
   ```python
   try:
       run_agent(test_id)
   except Exception as e:
       print(f"Agent failed for {test_id}: {e}")
       # 빈 결과로 계속 진행
   ```

4. **중간 결과 저장**: 긴 실행 시간을 위해 체크포인트 저장:
   ```python
   # 진행 상황 저장
   with open('progress.json', 'w') as f:
       json.dump({'completed': completed_ids}, f)
   ```

---

## English

### Overview

This guide explains how to evaluate CVDP benchmarks using an **external Agent application**. Instead of calling LLM APIs as functions, you can use your independent Agent program and only run evaluation.

### Workflow

```
1. Environment Setup (extract files from dataset.jsonl)
   ↓
2. Pass prompts to external Agent and execute
   ↓
3. Save Agent outputs as answers file
   ↓
4. Run evaluation only (using CVDP framework)
```

---

## Offline Environment Preparation Guide

### Overview

To use External Agents in an offline environment (limited internet access but pip/npm available), you need to prepare and transfer all necessary files beforehand.

### Step 1: Prepare Files in Online Environment

#### 1.1 Clone Repository and Download Dataset

```bash
# Clone CVDP benchmark repository
git clone https://github.com/nvidia-tcad/cvdp_benchmark.git
cd cvdp_benchmark

# Download dataset.jsonl from Hugging Face
# Method 1: Download via web browser
# https://huggingface.co/datasets/nvidia/cvdp-benchmark-dataset

# Method 2: Use huggingface-cli
pip install huggingface-hub
huggingface-cli download nvidia/cvdp-benchmark-dataset --repo-type dataset --local-dir ./dataset

# Copy needed dataset.jsonl to project root
cp dataset/cvdp_v1.0.1_nonagentic_code_generation_no_commercial.jsonl ./dataset.jsonl
```

#### 1.2 Download Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv_online
source venv_online/bin/activate  # Windows: venv_online\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Download dependencies (download only, don't install)
pip download -r requirements.txt -d ./offline_packages

# Download additional packages for Docker-free execution
pip download -r requirements-direct.txt -d ./offline_packages

# Remove duplicates and clean up (optional)
```

#### 1.3 Prepare Simulator and Tools

**Icarus Verilog (Recommended):**

```bash
# Download Ubuntu/Debian packages
mkdir -p offline_tools
cd offline_tools

# Download Icarus Verilog package
apt-get download iverilog
# Download dependency packages
apt-cache depends iverilog | grep Depends | awk '{print $2}' | xargs apt-get download

cd ..
```

**Or download tarball for building from source:**

```bash
mkdir -p offline_tools
cd offline_tools

# Download Icarus Verilog source
wget https://github.com/steveicarus/iverilog/archive/refs/tags/v12_0.tar.gz -O iverilog-12.0.tar.gz

cd ..
```

**NPM Packages (if External Agent uses Node.js):**

```bash
# If using Node.js-based External Agent
# If your project has package.json

mkdir -p offline_npm_packages
cd your_agent_directory

# Generate package-lock.json (if not exists)
npm install

# Create offline tarball
npm pack

# Or prepare offline packages via npm cache
npm install --prefer-offline
# Copy npm cache directory (~/.npm or %AppData%/npm-cache)
mkdir -p ../offline_npm_packages
cp -r ~/.npm ../offline_npm_packages/npm-cache

cd ..
```

#### 1.4 Create Complete Package

```bash
# Create package for offline transfer
cd ..
tar -czf cvdp_offline_package.tar.gz cvdp_benchmark/
```

### Step 2: Transfer Files to Offline Environment

```bash
# Transfer via USB, network drive, etc.
# Copy cvdp_offline_package.tar.gz to offline environment
```

### Step 3: Installation in Offline Environment

#### 3.1 Extract Package

```bash
# In offline environment
tar -xzf cvdp_offline_package.tar.gz
cd cvdp_benchmark
```

#### 3.2 Install Simulator

**Method 1: Install downloaded .deb packages (Ubuntu/Debian):**

```bash
cd offline_tools
sudo dpkg -i *.deb
# Fix dependencies if needed
sudo apt-get install -f

cd ..
```

**Method 2: Build from source:**

```bash
cd offline_tools
tar -xzf iverilog-12.0.tar.gz
cd iverilog-12_0
./configure
make
sudo make install

cd ../..
```

#### 3.3 Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies from offline packages
pip install --no-index --find-links=./offline_packages -r requirements.txt
pip install --no-index --find-links=./offline_packages -r requirements-direct.txt
```

**Install NPM Packages (if using Node.js-based Agent):**

```bash
# Method 1: Use npm cache
cp -r offline_npm_packages/npm-cache ~/.npm

cd your_agent_directory
npm install --offline

# Method 2: Use local tarball
cd your_agent_directory
npm install /path/to/your-agent-package.tgz

cd ..
```

#### 3.4 Configure Environment Variables

```bash
# Create .env file
cp .env.example .env

# Edit .env file if needed
# LLM API keys not required in offline environment (using answers file)
```

### Step 4: Run External Agent in Offline Environment

Once the offline environment is ready, follow the "Step-by-Step Guide" below.

**Key Notes:**
- No internet connection required (no LLM API calls)
- Save External Agent execution results as answers file
- Run evaluation locally only (using `-a` option)

### Checklist: Verify Offline Environment Setup

- [ ] CVDP benchmark repository copied
- [ ] dataset.jsonl file prepared
- [ ] Python dependency packages (offline_packages) prepared
- [ ] Icarus Verilog or Verilator installed
- [ ] Python virtual environment created and packages installed
- [ ] External Agent program prepared (if applicable)

### Troubleshooting (Offline)

**Issue: "Could not find a version" error during pip install**
```bash
# Solution: Check if wheel files are in offline_packages
ls offline_packages/

# If packages are missing, re-download in online environment
# pip download <package-name> -d ./offline_packages
```

**Issue: "command not found" when running Icarus Verilog**
```bash
# Solution: Check PATH
which iverilog

# Manually add to PATH if needed
export PATH=$PATH:/usr/local/bin
```

**Issue: cocotb cannot find simulator**
```bash
# Solution: Check SIM environment variable
export SIM=icarus

# Verify simulator is in PATH
which iverilog
```

**Issue: Network error during npm install**
```bash
# Solution: Use --offline or --prefer-offline flag
npm install --offline

# Or set npm registry to local
npm config set registry http://localhost:4873
```

### Automated Script Example: Offline Package Preparation

Script to run in online environment to prepare all necessary files at once:

```bash
#!/bin/bash
# prepare_offline_package.sh
# Run in online environment to prepare offline package

set -e

echo "=== CVDP Offline Package Preparation Started ==="

# 1. Assume repository is already cloned
REPO_DIR=$(pwd)
PACKAGE_DIR="${REPO_DIR}_offline_prepared"

echo "Working directory: $PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

# 2. Copy repository
echo "[1/6] Copying repository..."
rsync -av --exclude='.git' --exclude='venv*' --exclude='work*' \
  "$REPO_DIR/" "$PACKAGE_DIR/cvdp_benchmark/"

cd "$PACKAGE_DIR/cvdp_benchmark"

# 3. Download Python packages
echo "[2/6] Downloading Python packages..."
mkdir -p offline_packages
pip download -r requirements.txt -d ./offline_packages
pip download -r requirements-direct.txt -d ./offline_packages

# 4. Download dataset (requires huggingface-cli)
echo "[3/6] Downloading dataset..."
if command -v huggingface-cli &> /dev/null; then
    huggingface-cli download nvidia/cvdp-benchmark-dataset \
        --repo-type dataset --local-dir ./dataset
    cp dataset/cvdp_v1.0.1_nonagentic_code_generation_no_commercial.jsonl \
        ./dataset.jsonl
else
    echo "Warning: huggingface-cli not installed."
    echo "Please download manually from https://huggingface.co/datasets/nvidia/cvdp-benchmark-dataset"
fi

# 5. Download Icarus Verilog source
echo "[4/6] Downloading Icarus Verilog..."
mkdir -p offline_tools
cd offline_tools
if command -v wget &> /dev/null; then
    wget https://github.com/steveicarus/iverilog/archive/refs/tags/v12_0.tar.gz \
        -O iverilog-12.0.tar.gz
else
    echo "Warning: wget not installed."
    echo "Please download Icarus Verilog manually."
fi
cd ..

# 6. Create README
echo "[5/6] Creating offline installation guide..."
cat > OFFLINE_INSTALL.md << 'EOF'
# Offline Installation Guide

## 1. Install Simulator
```bash
cd offline_tools
tar -xzf iverilog-12.0.tar.gz
cd iverilog-12_0
./configure
make
sudo make install
cd ../..
```

## 2. Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --no-index --find-links=./offline_packages -r requirements.txt
pip install --no-index --find-links=./offline_packages -r requirements-direct.txt
```

## 3. Run
See "Step-by-Step Guide" section in EXTERNAL_AGENT_GUIDE.md
EOF

# 7. Compress
echo "[6/6] Compressing package..."
cd "$PACKAGE_DIR"
tar -czf cvdp_offline_package.tar.gz cvdp_benchmark/

echo ""
echo "=== Complete! ==="
echo "Created file: $PACKAGE_DIR/cvdp_offline_package.tar.gz"
echo "Transfer this file to your offline environment."
```

Usage:
```bash
chmod +x prepare_offline_package.sh
./prepare_offline_package.sh
```

---

### Step-by-Step Guide

#### Step 1: Environment Setup (File Extraction)

First, extract necessary files from dataset.jsonl:

```python
import json
import os

# Read dataset.jsonl
with open('dataset.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)
        test_id = data['id']
        
        # Create workspace
        work_dir = f"external_agent_workspace/{test_id}"
        os.makedirs(work_dir, exist_ok=True)
        
        # Save prompt
        prompt = data['input']['prompt']
        with open(f"{work_dir}/prompt.txt", 'w') as pf:
            pf.write(prompt)
        
        # Save context files (if any)
        if 'context' in data['input']:
            for filename, content in data['input']['context'].items():
                filepath = os.path.join(work_dir, filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'w') as cf:
                    cf.write(content)
        
        print(f"Prepared workspace for {test_id}")
```

#### Step 2: Run External Agent

Run your external Agent for each test case:

```bash
# Example: Run agent for each test case
for test_dir in external_agent_workspace/*/; do
    test_id=$(basename "$test_dir")
    
    # Run agent with prompt
    my-agent \
        --prompt "$test_dir/prompt.txt" \
        --workspace "$test_dir" \
        --output "$test_dir/solution.v"
    
    echo "Completed $test_id"
done
```

Or in Python:

```python
import subprocess

workspace_dir = "external_agent_workspace"
for test_id in os.listdir(workspace_dir):
    test_path = os.path.join(workspace_dir, test_id)
    
    # Read prompt
    with open(f"{test_path}/prompt.txt", 'r') as f:
        prompt = f.read()
    
    # Run external agent
    result = subprocess.run([
        'my-agent',
        '--prompt', prompt,
        '--workspace', test_path,
        '--output', f'{test_path}/solution.v'
    ])
    
    print(f"Agent completed {test_id} with code {result.returncode}")
```

#### Step 3: Create Answers File

Convert Agent outputs to CVDP-compatible answers format:

```python
import json

answers = []

# Read original dataset
with open('dataset.jsonl', 'r') as f:
    dataset = [json.loads(line) for line in f]

# Convert each test case result to answers format
for data in dataset:
    test_id = data['id']
    work_dir = f"external_agent_workspace/{test_id}"
    
    # Read Agent-generated solution
    solution_files = {}
    
    # Example: Read RTL file
    solution_path = f"{work_dir}/solution.v"
    if os.path.exists(solution_path):
        with open(solution_path, 'r') as sf:
            # Check expected output file path from dataset
            if 'output' in data and 'context' in data['output']:
                # Use the first output file path
                output_key = list(data['output']['context'].keys())[0]
                solution_files[output_key] = sf.read()
    
    # Answers format: {test_id: {input: ..., output: {context: ...}}}
    answer_entry = {
        test_id: {
            'input': data['input'],
            'output': {
                'response': '',  # Optional
                'context': solution_files
            }
        }
    }
    
    answers.append(answer_entry)

# Save answers file (JSONL format)
with open('my_agent_answers.jsonl', 'w') as f:
    for answer in answers:
        f.write(json.dumps(answer) + '\n')

print(f"Created answers file with {len(answers)} entries")
```

#### Step 4: Run Evaluation Only

Now evaluate the Agent's results:

```bash
# Run evaluation only (without LLM calls)
python run_benchmark.py \
    -f dataset.jsonl \
    -a my_agent_answers.jsonl \
    -p work_external_agent

# Check results
cat work_external_agent/report.txt
```

### Answers File Format

The answers file is in JSONL format, where each line has this structure:

```json
{
  "cvdp_copilot_test_0001": {
    "input": {
      "prompt": "Original prompt...",
      "context": {}
    },
    "output": {
      "response": "",
      "context": {
        "rtl/module.v": "Verilog code generated by Agent..."
      }
    }
  }
}
```

**Important:**
- Each line contains one test case result
- Key is the test case ID
- `output.context` contains files generated by Agent
- File paths must match keys in original dataset's `output.context`

### Complete Automation Script Example

See the Korean section above for a complete Python automation script that handles all 4 steps.

### Tips and Best Practices

1. **Path Matching**: Agent output file paths must exactly match dataset's `output.context` keys.

2. **Parallel Processing**: Process multiple test cases concurrently:
   ```python
   from concurrent.futures import ThreadPoolExecutor
   
   with ThreadPoolExecutor(max_workers=4) as executor:
       executor.map(run_agent_for_test, test_ids)
   ```

3. **Error Handling**: Allow evaluation of partial results if Agent fails:
   ```python
   try:
       run_agent(test_id)
   except Exception as e:
       print(f"Agent failed for {test_id}: {e}")
       # Continue with empty result
   ```

4. **Checkpoint Saving**: Save progress for long runs:
   ```python
   # Save progress
   with open('progress.json', 'w') as f:
       json.dump({'completed': completed_ids}, f)
   ```

## Command Reference

```bash
# Full command with all options
python run_benchmark.py \
    -f dataset.jsonl \           # Input dataset
    -a my_agent_answers.jsonl \  # Agent results
    -p work_external_agent \      # Output directory
    -t 4                          # Parallel threads (optional)

# For multi-sample evaluation
python run_samples.py \
    -f dataset.jsonl \
    -a my_agent_answers.jsonl \
    -n 5 \                        # Number of samples
    -k 1 \                        # Pass@k threshold
    -p work_multi_sample
```
