# CVDP Benchmark - Offline Quick Reference

**빠른 참조 카드 | Quick Reference Card**

## 오프라인 환경 준비 (Preparing Offline Environment)

### 1️⃣ 온라인 환경에서 (In Online Environment)

```bash
# 준비 스크립트 실행
./tools/prepare_offline_package.sh

# 생성된 파일을 오프라인 환경으로 전송
# cvdp_offline_package.tar.gz
```

### 2️⃣ 오프라인 환경에서 (In Offline Environment)

```bash
# 압축 해제
tar -xzf cvdp_offline_package.tar.gz
cd cvdp_benchmark

# 시뮬레이터 설치
cd offline_tools
tar -xzf iverilog-12_0.tar.gz
cd iverilog-12_0
./configure && make && sudo make install
cd ../..

# Python 환경 설정
python3 -m venv venv
source venv/bin/activate
pip install --no-index --find-links=./offline_packages -r requirements.txt
pip install --no-index --find-links=./offline_packages -r requirements-direct.txt

# 환경 설정
cp .env.example .env
```

### 3️⃣ External Agent 평가 (External Agent Evaluation)

```bash
# 1. 작업공간 준비
python -c "
import json, os
with open('dataset.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)
        test_id = data['id']
        work_dir = f'external_agent_workspace/{test_id}'
        os.makedirs(work_dir, exist_ok=True)
        with open(f'{work_dir}/prompt.txt', 'w') as pf:
            pf.write(data['input']['prompt'])
"

# 2. Agent 실행 (예시)
for dir in external_agent_workspace/*/; do
    test_id=$(basename "$dir")
    my-agent --prompt "$dir/prompt.txt" --output "$dir/solution.v"
done

# 3. Answers 파일 생성
python -c "
import json, os
answers = []
with open('dataset.jsonl', 'r') as f:
    dataset = [json.loads(line) for line in f]
for data in dataset:
    test_id = data['id']
    solution_files = {}
    # Agent 출력 파일 읽기 및 매핑
    # ... (EXTERNAL_AGENT_GUIDE.md 참조)
    answers.append({test_id: {'input': data['input'], 'output': {'response': '', 'context': solution_files}}})
with open('answers.jsonl', 'w') as f:
    for a in answers: f.write(json.dumps(a) + '\n')
"

# 4. 평가 실행
python run_benchmark.py -f dataset.jsonl -a answers.jsonl -p work_results
cat work_results/report.txt
```

## 체크리스트 (Checklist)

### 온라인 환경 (Online)
- [ ] CVDP 저장소 클론
- [ ] `prepare_offline_package.sh` 실행
- [ ] `cvdp_offline_package.tar.gz` 생성 확인
- [ ] 오프라인 환경으로 전송

### 오프라인 환경 (Offline)
- [ ] 패키지 압축 해제
- [ ] Icarus Verilog 빌드 및 설치
- [ ] Python 가상환경 생성
- [ ] 오프라인 패키지로부터 pip 설치
- [ ] dataset.jsonl 파일 확인
- [ ] External Agent 준비 완료

### 실행 (Execution)
- [ ] 작업공간 디렉토리 생성
- [ ] Agent 실행 및 결과 수집
- [ ] Answers 파일 생성
- [ ] 평가 실행
- [ ] 결과 확인

## 문제 해결 (Troubleshooting)

| 문제 (Issue) | 해결 (Solution) |
|------------|---------------|
| `iverilog: command not found` | `export PATH=$PATH:/usr/local/bin` |
| `Could not find a version` (pip) | 온라인 환경에서 재다운로드 필요 |
| `SIM not found` (cocotb) | `export SIM=icarus` |
| npm 오류 | `npm install --offline` |

## 자세한 문서 (Detailed Documentation)

- **EXTERNAL_AGENT_GUIDE.md** - 전체 가이드 (Complete Guide)
  - "오프라인 환경 준비 가이드" 섹션 (Offline Environment Setup section)
- **OFFLINE_INSTALL.md** - 오프라인 패키지에 포함된 설치 가이드
- **QUICKSTART_DOCKER_FREE.md** - Docker 없이 빠른 시작
- **README.md** - 프로젝트 개요

## 도움말 (Help)

```bash
# 스크립트 도움말
./tools/prepare_offline_package.sh --help

# Python 스크립트 도움말
python run_benchmark.py --help
python run_direct.py --help
```

---

**참고**: 이 카드는 빠른 참조용입니다. 자세한 내용은 EXTERNAL_AGENT_GUIDE.md를 참조하세요.

**Note**: This card is for quick reference. See EXTERNAL_AGENT_GUIDE.md for detailed instructions.
