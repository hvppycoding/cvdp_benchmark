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
