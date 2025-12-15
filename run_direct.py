#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Direct Test Runner - Run CVDP tests without Docker

This script allows running CVDP benchmark tests directly on the host system
without using Docker. It extracts test files from dataset.jsonl and runs
them using the installed Verilog simulator (Icarus Verilog or Verilator).

Usage:
    # Run single test case
    python run_direct.py -f dataset.jsonl -i cvdp_copilot_lfsr_0001
    
    # Run all test cases
    python run_direct.py -f dataset.jsonl
    
    # Use custom output directory
    python run_direct.py -f dataset.jsonl -p work_custom
"""

import argparse
import json
import os
import sys
import subprocess
import shutil
import time

# Default timeout for test execution (can be overridden with -t flag)
DEFAULT_TIMEOUT = 300  # 5 minutes

def normalize_dataset_path(path_str, base_dir):
    """
    Normalize paths from dataset.jsonl to absolute paths.
    
    Handles Docker-specific paths used in CVDP datasets and converts them
    to absolute paths based on the extraction directory.
    
    CVDP Docker Path Conventions:
    - /code/ : Main working directory in Docker containers
    - /src/  : Source files directory  
    - /rundir/ : Test execution directory
    
    These paths are used in dataset.jsonl files to specify locations
    within the Docker container, and need to be converted to actual
    filesystem paths for direct execution.
    
    Args:
        path_str: Path string that may contain Docker-specific prefixes
        base_dir: Base directory where files are extracted
        
    Returns:
        Normalized absolute path
    """
    # Docker path patterns used in CVDP datasets
    # These patterns appear at the start of path strings in .env files
    docker_patterns = ['/code/', '/src/', '/rundir/']
    
    for pattern in docker_patterns:
        if path_str.startswith(pattern):
            # Replace Docker path prefix with actual base directory
            # Only replace the first occurrence to avoid issues with paths
            # that might contain the pattern multiple times
            path_str = path_str.replace(pattern, f'{os.path.abspath(base_dir)}/', 1)
            break
    
    return path_str

def calculate_pass_rate(passed, total):
    """Calculate pass rate percentage, handling empty dataset case."""
    if total > 0:
        return f"{passed/total*100:.1f}%"
    return "N/A (no tests run)"

def parse_env_file(env_content):
    """Parse .env file content and return a dictionary of environment variables."""
    env_vars = {}
    for line in env_content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            env_vars[key.strip()] = value.strip()
    return env_vars

def extract_test_files(data, base_dir):
    """Extract test files from dataset entry to base directory."""
    test_id = data['id']
    
    # Create directory structure
    dirs = ['rtl', 'verif', 'docs', 'src', 'rundir']
    for d in dirs:
        os.makedirs(os.path.join(base_dir, d), exist_ok=True)
    
    # Extract RTL/solution files from output
    if 'output' in data and 'context' in data['output']:
        for filepath, content in data['output']['context'].items():
            full_path = os.path.join(base_dir, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
            print(f"  Created: {filepath}")
    
    # Extract test harness files
    if 'harness' in data and 'files' in data['harness']:
        for filepath, content in data['harness']['files'].items():
            # Skip Dockerfile and docker-compose.yml as we won't use them
            if filepath in ['Dockerfile', 'docker-compose.yml']:
                continue
                
            full_path = os.path.join(base_dir, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
            print(f"  Created: {filepath}")
    
    return test_id

def run_test_direct(base_dir, timeout=DEFAULT_TIMEOUT):
    """Run test directly without Docker using cocotb + pytest.
    
    Args:
        base_dir: Base directory containing extracted test files
        timeout: Timeout in seconds for test execution (default: 300)
        
    Returns:
        Tuple of (success, log_file, execution_time)
    """
    
    # Parse environment variables from src/.env
    env_file = os.path.join(base_dir, 'src', '.env')
    if not os.path.exists(env_file):
        print(f"  ERROR: Environment file not found: {env_file}")
        return False, "Environment file not found", 0
    
    with open(env_file, 'r') as f:
        env_vars = parse_env_file(f.read())
    
    # Set up environment
    env = os.environ.copy()
    
    # Required cocotb environment variables
    env['SIM'] = env_vars.get('SIM', 'icarus')
    env['TOPLEVEL_LANG'] = env_vars.get('TOPLEVEL_LANG', 'verilog')
    env['TOPLEVEL'] = env_vars.get('TOPLEVEL', '')
    env['MODULE'] = env_vars.get('MODULE', '')
    
    # Convert relative paths to absolute paths
    verilog_sources = env_vars.get('VERILOG_SOURCES', '')
    if verilog_sources:
        # Use the utility function for path normalization
        verilog_sources = normalize_dataset_path(verilog_sources, base_dir)
        env['VERILOG_SOURCES'] = verilog_sources
    
    # Set PYTHONPATH to include src directory
    src_path = os.path.join(base_dir, 'src')
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f"{src_path}:{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = src_path
    
    # Check if simulator is available
    sim = env['SIM']
    simulator_cmd = 'iverilog' if sim == 'icarus' else sim
    if not shutil.which(simulator_cmd):
        print(f"  ERROR: Simulator '{simulator_cmd}' not found in PATH")
        print(f"  Please install it: sudo apt-get install {simulator_cmd}")
        return False, f"Simulator {simulator_cmd} not installed", 0
    
    # Run pytest from the base directory
    print(f"  Running tests with {sim} simulator...")
    start_time = time.time()
    
    try:
        # Run pytest on test_runner.py
        test_runner = os.path.join(base_dir, 'src', 'test_runner.py')
        
        result = subprocess.run(
            ['pytest', '-s', '--log-cli-level=INFO', 
             '-o', f'cache_dir={os.path.join(base_dir, "rundir", ".cache")}',
             test_runner, '-v'],
            env=env,
            cwd=os.path.join(base_dir, 'rundir'),
            capture_output=True,
            text=True,
            timeout=timeout  # Use configurable timeout
        )
        
        execution_time = time.time() - start_time
        
        # Save output
        log_file = os.path.join(base_dir, 'test_output.log')
        with open(log_file, 'w') as f:
            f.write("=== STDOUT ===\n")
            f.write(result.stdout)
            f.write("\n=== STDERR ===\n")
            f.write(result.stderr)
        
        success = result.returncode == 0
        
        if success:
            print(f"  ✓ Tests passed ({execution_time:.2f}s)")
        else:
            print(f"  ✗ Tests failed ({execution_time:.2f}s)")
            print(f"  See log: {log_file}")
        
        return success, log_file, execution_time
        
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        print(f"  ✗ Test timeout ({execution_time:.2f}s)")
        return False, "Timeout", execution_time
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"  ✗ Error running test: {e}")
        return False, str(e), execution_time

def main():
    parser = argparse.ArgumentParser(
        description='Run CVDP tests directly without Docker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run single test case
  python run_direct.py -f dataset.jsonl -i cvdp_copilot_lfsr_0001
  
  # Run all test cases
  python run_direct.py -f dataset.jsonl
  
  # Use custom output directory
  python run_direct.py -f dataset.jsonl -p work_custom
        """
    )
    
    parser.add_argument('-f', '--file', required=True,
                        help='Path to dataset.jsonl file')
    parser.add_argument('-i', '--id', 
                        help='Run specific test case by ID')
    parser.add_argument('-p', '--prefix', default='work_direct',
                        help='Output directory prefix (default: work_direct)')
    parser.add_argument('-t', '--timeout', type=int, default=DEFAULT_TIMEOUT,
                        help=f'Timeout per test in seconds (default: {DEFAULT_TIMEOUT})')
    
    args = parser.parse_args()
    
    # Check prerequisites
    print("Checking prerequisites...")
    
    # Check if pytest is available
    if not shutil.which('pytest'):
        print("ERROR: pytest not found. Please install it:")
        print("  pip install pytest cocotb cocotb-bus")
        return 1
    
    # Check if at least one simulator is available
    has_simulator = False
    for sim in ['iverilog', 'verilator']:
        if shutil.which(sim):
            has_simulator = True
            print(f"  ✓ Found simulator: {sim}")
            break
    
    if not has_simulator:
        print("ERROR: No Verilog simulator found. Please install one:")
        print("  sudo apt-get install iverilog  # Icarus Verilog")
        print("  sudo apt-get install verilator  # Verilator")
        return 1
    
    print(f"  ✓ pytest found")
    print()
    
    # Read dataset
    print(f"Reading dataset: {args.file}")
    if not os.path.exists(args.file):
        print(f"ERROR: File not found: {args.file}")
        return 1
    
    with open(args.file, 'r') as f:
        dataset = [json.loads(line) for line in f if line.strip()]
    
    print(f"  Found {len(dataset)} test cases")
    print()
    
    # Filter by ID if specified
    if args.id:
        dataset = [d for d in dataset if d['id'] == args.id]
        if not dataset:
            print(f"ERROR: Test case '{args.id}' not found in dataset")
            return 1
        print(f"  Running single test: {args.id}")
    else:
        print(f"  Running all {len(dataset)} test cases")
    print()
    
    # Create output directory
    os.makedirs(args.prefix, exist_ok=True)
    
    # Track results
    results = {}
    passed = 0
    failed = 0
    
    # Process each test case
    for i, data in enumerate(dataset, 1):
        test_id = data['id']
        print(f"[{i}/{len(dataset)}] Processing: {test_id}")
        
        # Create test directory
        test_dir = os.path.join(args.prefix, test_id)
        os.makedirs(test_dir, exist_ok=True)
        
        # Extract files
        print(f"  Extracting files...")
        extract_test_files(data, test_dir)
        
        # Run test
        success, log, execution_time = run_test_direct(test_dir, timeout=args.timeout)
        
        # Record result
        results[test_id] = {
            'success': success,
            'log': log,
            'execution_time': execution_time,
            'categories': data.get('categories', [])
        }
        
        if success:
            passed += 1
        else:
            failed += 1
        
        print()
    
    # Generate report
    report_file = os.path.join(args.prefix, 'report.txt')
    with open(report_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("CVDP Direct Test Execution Report\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Total Tests: {len(dataset)}\n")
        f.write(f"Passed: {passed}\n")
        f.write(f"Failed: {failed}\n")
        f.write(f"Pass Rate: {calculate_pass_rate(passed, len(dataset))}\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("Individual Results\n")
        f.write("=" * 80 + "\n\n")
        
        for test_id, result in results.items():
            status = "PASS" if result['success'] else "FAIL"
            f.write(f"{test_id}: {status} ({result['execution_time']:.2f}s)\n")
            if not result['success']:
                f.write(f"  Log: {result['log']}\n")
            f.write("\n")
    
    # Print summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(dataset)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Pass Rate: {calculate_pass_rate(passed, len(dataset))}")
    print()
    print(f"Report saved to: {report_file}")
    print("=" * 80)
    
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
