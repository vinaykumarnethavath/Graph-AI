"""
Test Runner Script
Runs pytest with various configurations
"""

import sys
import subprocess


def run_all_tests():
    """Run all tests"""
    print("Running all tests...")
    result = subprocess.run(["pytest", "tests/", "-v"], capture_output=False)
    return result.returncode


def run_api_tests():
    """Run only API tests"""
    print("Running API tests...")
    result = subprocess.run(["pytest", "tests/", "-m", "api", "-v"], capture_output=False)
    return result.returncode


def run_query_tests():
    """Run only query tests"""
    print("Running query tests...")
    result = subprocess.run(["pytest", "tests/", "-m", "query", "-v"], capture_output=False)
    return result.returncode


def run_edge_tests():
    """Run only edge case tests"""
    print("Running edge case tests...")
    result = subprocess.run(["pytest", "tests/", "-m", "edge", "-v"], capture_output=False)
    return result.returncode


def run_llm_tests():
    """Run only LLM tests"""
    print("Running LLM tests...")
    result = subprocess.run(["pytest", "tests/", "-m", "llm", "-v"], capture_output=False)
    return result.returncode


def run_fast_tests():
    """Run fast tests (exclude slow LLM tests)"""
    print("Running fast tests (excluding LLM)...")
    result = subprocess.run(["pytest", "tests/", "-m", "not slow", "-v"], capture_output=False)
    return result.returncode


def run_with_coverage():
    """Run tests with coverage report"""
    print("Running tests with coverage...")
    result = subprocess.run([
        "pytest",
        "tests/",
        "--cov=backend.services",
        "--cov=backend.api",
        "--cov-report=html",
        "--cov-report=term",
        "-v"
    ], capture_output=False)
    return result.returncode


def main():
    """Main test runner"""
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py [all|api|query|edge|llm|fast|coverage]")
        print("\nOptions:")
        print("  all      - Run all tests")
        print("  api      - Run API endpoint tests")
        print("  query    - Run query engine tests")
        print("  edge     - Run edge case tests")
        print("  llm      - Run LLM integration tests")
        print("  fast     - Run fast tests (no LLM)")
        print("  coverage - Run with coverage report")
        sys.exit(1)
    
    option = sys.argv[1].lower()
    
    runners = {
        "all": run_all_tests,
        "api": run_api_tests,
        "query": run_query_tests,
        "edge": run_edge_tests,
        "llm": run_llm_tests,
        "fast": run_fast_tests,
        "coverage": run_with_coverage
    }
    
    if option not in runners:
        print(f"Unknown option: {option}")
        print("Valid options: all, api, query, edge, llm, fast, coverage")
        sys.exit(1)
    
    exit_code = runners[option]()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
