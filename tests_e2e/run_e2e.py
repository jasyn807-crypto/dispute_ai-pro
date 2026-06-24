import argparse
import sys
import subprocess
import os

def check_pytest_installed():
    try:
        import pytest
        return True
    except ImportError:
        return False

def main():
    parser = argparse.ArgumentParser(description="E2E Test Runner for Credit Repair SaaS")
    
    parser.add_argument(
        "--backend-url",
        default=None,
        help="URL of the running backend (if not provided, a mock backend will start automatically)"
    )
    parser.add_argument(
        "-k",
        dest="expression",
        default=None,
        help="Only run tests which match the given substring expression (pytest -k)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Increase verbosity of pytest output"
    )
    
    args, unknown = parser.parse_known_args()
    
    # Locate tests_e2e/test_cases directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    tests_dir = os.path.join(base_dir, "test_cases")
    if not os.path.exists(tests_dir):
        tests_dir = os.path.join(os.getcwd(), "credit_repair_saas", "tests_e2e", "test_cases")
        
    if not os.path.exists(tests_dir):
        print(f"[E2E Error] Test cases directory not found at: {tests_dir}")
        sys.exit(1)
        
    # Check if pytest is installed
    if not check_pytest_installed():
        print("[E2E Error] pytest is not installed in the current Python environment.")
        print("Please install pytest and its dependencies (e.g., httpx) before running E2E tests.")
        sys.exit(1)
        
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest", tests_dir]
    
    if args.backend_url:
        cmd.extend(["--backend-url", args.backend_url])
        
    if args.expression:
        cmd.extend(["-k", args.expression])
        
    if args.verbose:
        cmd.append("-v")
        
    # Pass through any other unknown arguments to pytest
    if unknown:
        cmd.extend(unknown)
        
    print(f"[E2E] Running command: {' '.join(cmd)}")
    
    try:
        # Run pytest as a subprocess
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n[E2E] Testing interrupted by user.")
        sys.exit(1)

if __name__ == "__main__":
    main()
