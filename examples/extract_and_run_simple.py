#!/usr/bin/env python3

"""
Simple example showing how to extract and run a single test case from dataset.jsonl
without any Docker dependencies.

This is a minimal educational example to demonstrate the core concept.
For production use, see run_direct.py
"""

import json
import os
import subprocess
import sys

def normalize_dataset_path(path_str, base_dir):
    """
    Normalize paths from dataset.jsonl to absolute paths.
    
    Handles Docker-specific paths used in CVDP datasets.
    See run_direct.py for full documentation.
    """
    docker_patterns = ['/code/', '/src/', '/rundir/']
    
    for pattern in docker_patterns:
        if path_str.startswith(pattern):
            # Only replace first occurrence
            path_str = path_str.replace(pattern, f'{os.path.abspath(base_dir)}/', 1)
            break
    
    return path_str

def extract_and_run_example():
    """Extract first test case and show how to run it."""
    
    # Example dataset file
    dataset_file = 'example_dataset/cvdp_v1.0.1_example_nonagentic_code_generation_no_commercial_with_solutions.jsonl'
    
    if not os.path.exists(dataset_file):
        print(f"ERROR: Dataset file not found: {dataset_file}")
        print("Please run this script from the repository root directory.")
        return 1
    
    print("=" * 80)
    print("Simple Dataset.jsonl Test Extraction Example")
    print("=" * 80)
    print()
    
    # Read first test case
    print("Step 1: Reading dataset.jsonl...")
    with open(dataset_file, 'r') as f:
        data = json.loads(f.readline())
    
    test_id = data['id']
    print(f"  Test ID: {test_id}")
    print(f"  Categories: {data.get('categories', [])}")
    print()
    
    # Create output directory
    print("Step 2: Creating directory structure...")
    base_dir = f"example_manual_run/{test_id}"
    
    for directory in ['rtl', 'verif', 'docs', 'src', 'rundir']:
        os.makedirs(os.path.join(base_dir, directory), exist_ok=True)
        print(f"  Created: {directory}/")
    print()
    
    # Extract solution files (RTL)
    print("Step 3: Extracting RTL/solution files...")
    if 'output' in data and 'context' in data['output']:
        for filepath, content in data['output']['context'].items():
            full_path = os.path.join(base_dir, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
            print(f"  Saved: {filepath} ({len(content)} bytes)")
    print()
    
    # Extract test files
    print("Step 4: Extracting test harness files...")
    if 'harness' in data and 'files' in data['harness']:
        for filepath, content in data['harness']['files'].items():
            if filepath in ['Dockerfile', 'docker-compose.yml']:
                print(f"  Skipped: {filepath} (not needed for direct execution)")
                continue
            
            full_path = os.path.join(base_dir, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
            print(f"  Saved: {filepath} ({len(content)} bytes)")
    print()
    
    # Parse environment variables
    print("Step 5: Reading test configuration...")
    env_file = os.path.join(base_dir, 'src', '.env')
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                print(f"  {line}")
    print()
    
    # Generate run instructions
    print("=" * 80)
    print("Files extracted successfully!")
    print("=" * 80)
    print()
    print("To run the test manually:")
    print()
    print(f"  cd {base_dir}/rundir")
    print()
    print("  # Set environment variables from src/.env")
    print("  export SIM=icarus")
    print("  export TOPLEVEL_LANG=verilog")
    print(f"  export VERILOG_SOURCES=$(cd .. && pwd)/rtl/*.sv")
    print("  export TOPLEVEL=lfsr_8bit  # or your module name")
    print("  export MODULE=test_lfsr    # or your test module name")
    print(f"  export PYTHONPATH=$(cd ../src && pwd)")
    print()
    print("  # Run test")
    print("  pytest -s ../src/test_runner.py -v")
    print()
    print("=" * 80)
    print()
    
    # Try to run automatically if pytest is available
    import shutil
    if shutil.which('pytest') and shutil.which('iverilog'):
        print("Prerequisites found! Attempting to run test automatically...")
        print()
        
        # Setup environment
        env = os.environ.copy()
        env_file_path = os.path.join(base_dir, 'src', '.env')
        
        with open(env_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Normalize Docker paths using the utility function
                    value = normalize_dataset_path(value, base_dir)
                    
                    env[key] = value
        
        # Set PYTHONPATH
        env['PYTHONPATH'] = os.path.join(base_dir, 'src')
        
        # Run pytest
        test_runner = os.path.join(base_dir, 'src', 'test_runner.py')
        
        print(f"Running: pytest -s {test_runner} -v")
        print()
        
        try:
            result = subprocess.run(
                ['pytest', '-s', '--log-cli-level=INFO', test_runner, '-v'],
                env=env,
                cwd=os.path.join(base_dir, 'rundir'),
                timeout=120
            )
            
            print()
            if result.returncode == 0:
                print("✓ Test PASSED!")
            else:
                print("✗ Test FAILED!")
            
            return result.returncode
            
        except subprocess.TimeoutExpired:
            print("✗ Test timed out!")
            return 1
        except Exception as e:
            print(f"✗ Error running test: {e}")
            return 1
    else:
        missing = []
        if not shutil.which('pytest'):
            missing.append('pytest (pip install pytest cocotb cocotb-bus)')
        if not shutil.which('iverilog'):
            missing.append('iverilog (sudo apt-get install iverilog)')
        
        print("Prerequisites missing for automatic execution:")
        for m in missing:
            print(f"  - {m}")
        print()
        print("Install prerequisites and run manually using the commands above.")
        
        return 0

if __name__ == '__main__':
    sys.exit(extract_and_run_example())
