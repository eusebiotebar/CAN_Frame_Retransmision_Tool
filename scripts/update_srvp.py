#!/usr/bin/env python3
"""
Script mejorado para actualizar el documento SRVP con resultados de tests.
Corrige los problemas identificados en la versión original.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

# Define paths
ROOT_DIR = Path(__file__).parent.parent
SRVP_PATH = ROOT_DIR / "resources" / "docs" / "srvp.md"
OUTPUT_PATH = ROOT_DIR / "resources" / "docs" / "srvp_test.md"
REPORT_PATH = ROOT_DIR / "resources" / "docs" / "report.json"
TESTS_DIR = ROOT_DIR / "tests"

def check_pytest_available():
    """Check if pytest is available."""
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"pytest available: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print("ERROR: pytest is not available.")
        print("Install with: pip install pytest pytest-json-report")
        return False

def run_tests():
    """Run pytest and generate a JSON report."""
    print("Running tests...")
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest",  # Use sys.executable to ensure correct Python
                "--json-report",
                f"--json-report-file={REPORT_PATH}",
                str(TESTS_DIR),
                "-v"  # Verbose output for debugging
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"Test report generated at {REPORT_PATH}")
        print("pytest stdout:", result.stdout[-500:])  # Last 500 chars
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR running pytest: {e}")
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)
        return False

def parse_test_report():
    """Parse the JSON test report to get test outcomes."""
    print("Parsing test report...")
    if not REPORT_PATH.exists():
        raise FileNotFoundError(f"Test report not found at {REPORT_PATH}")

    with open(REPORT_PATH, encoding='utf-8') as f:
        report = json.load(f)

    test_outcomes = {}
    for test in report.get("tests", []):
        test_outcomes[test["nodeid"]] = test["outcome"]
    
    print(f"Found {len(test_outcomes)} test results")
    return test_outcomes

def extract_req_ids_from_docstrings():
    """Extract requirement IDs from test function docstrings."""
    print("Extracting requirement IDs from test files...")
    req_to_tests = {}
    
    for test_file in TESTS_DIR.glob("test_*.py"):
        print(f"  Processing {test_file.name}...")
        content = test_file.read_text(encoding='utf-8')
        
        # IMPROVED REGEX: More flexible whitespace handling
        # Allows for any amount of whitespace and newlines between function def and docstring
        pattern = r'def (test_\w+)\([^)]*\):[\s\S]*?"""([\s\S]*?)"""'
        
        for match in re.finditer(pattern, content):
            test_name = match.group(1)
            docstring = match.group(2)
            # Full nodeid format to match pytest output
            full_test_name = f"tests/{test_file.name}::{test_name}"

            # Find all REQ-FUNC IDs in the docstring
            covered_reqs = re.findall(r"REQ-FUNC-\w+-\d{3}", docstring)
            for req_id in covered_reqs:
                if req_id not in req_to_tests:
                    req_to_tests[req_id] = []
                req_to_tests[req_id].append(full_test_name)
                print(f"    {req_id} -> {test_name}")

    print(f"Found {len(req_to_tests)} requirements with associated tests")
    return req_to_tests

def get_requirement_statuses(test_outcomes, req_to_tests):
    """Determine the status of each requirement based on test outcomes."""
    print("Determining requirement statuses...")
    req_statuses = {}
    
    for req_id, test_names in req_to_tests.items():
        outcomes = [test_outcomes.get(name, "skipped") for name in test_names]
        print(f"  {req_id}: tests={test_names}, outcomes={outcomes}")
        
        # A requirement is 'Failed' if any of its tests fail.
        if "failed" in outcomes:
            req_statuses[req_id] = "\\[x] Failed"
        # It is 'Verified' only if all of its tests pass.
        elif outcomes and all(o == "passed" for o in outcomes):
            req_statuses[req_id] = "\\[x] Verified"
        # Otherwise, the status is not determined
        else:
            print(f"    No clear status for {req_id} (outcomes: {outcomes})")
    
    print(f"Determined status for {len(req_statuses)} requirements")
    return req_statuses

def update_srvp_document(req_statuses):
    """Update the SRVP document with the new requirement statuses."""
    print(f"Updating SRVP document: {SRVP_PATH}")
    content = SRVP_PATH.read_text(encoding="utf-8")

    lines = content.splitlines()
    new_lines = []
    updates_made = 0

    # IMPROVED REGEX: More flexible status matching for all checkbox formats
    req_line_pattern = re.compile(
        r'\|\s*(REQ-FUNC-\w+-\d{3})\s*\|\s*Test\s*\|.*?\|\s*'
        r'(\\?\[[\sx]\] (?:Not Started|Verified|Failed)|Verified|Failed|'
        r'\\?\[ \\?\] Not Started)\s*\|'
    )

    for line in lines:
        match = req_line_pattern.search(line)
        if match:
            req_id = match.group(1)
            old_status = match.group(2)
            if req_id in req_statuses:
                new_status = req_statuses[req_id]
                # Replace the old status with the new one
                new_line = line.replace(old_status, new_status)
                new_lines.append(new_line)
                print(f"  - Updated {req_id}: {old_status} -> {new_status}")
                updates_made += 1
            else:
                new_lines.append(line)  # Keep line as is if no status found
        else:
            new_lines.append(line)

    OUTPUT_PATH.write_text("\n".join(new_lines), encoding="utf-8")
    print(f"SRVP document updated and saved to {OUTPUT_PATH}")
    print(f"Total updates made: {updates_made}")

def main():
    """Main function to run the entire process."""
    print("=== CAN Frame Retransmission Tool - SRVP Update Script ===")
    
    # Check prerequisites
    if not check_pytest_available():
        return 1
    
    if not SRVP_PATH.exists():
        print(f"ERROR: SRVP file not found: {SRVP_PATH}")
        return 1
    
    if not TESTS_DIR.exists():
        print(f"ERROR: Tests directory not found: {TESTS_DIR}")
        return 1
    
    try:
        # Step 1: Run tests
        if not run_tests():
            print("Failed to run tests")
            return 1
        
        # Step 2: Parse test results
        test_outcomes = parse_test_report()
        print("\n--- DEBUG: TEST OUTCOMES ---")
        for nodeid, outcome in list(test_outcomes.items())[:5]:  # Show first 5
            print(f"  {nodeid}: {outcome}")
        if len(test_outcomes) > 5:
            print(f"  ... and {len(test_outcomes) - 5} more")

        # Step 3: Extract requirement mappings
        req_to_tests = extract_req_ids_from_docstrings()
        print("\n--- DEBUG: REQ TO TESTS MAPPING ---")
        for req_id, tests in list(req_to_tests.items())[:5]:  # Show first 5
            print(f"  {req_id}: {tests}")
        if len(req_to_tests) > 5:
            print(f"  ... and {len(req_to_tests) - 5} more")

        # Step 4: Determine requirement statuses
        req_statuses = get_requirement_statuses(test_outcomes, req_to_tests)
        print("\n--- DEBUG: FINAL REQ STATUSES ---")
        for req_id, status in req_statuses.items():
            print(f"  {req_id}: {status}")

        # Step 5: Update SRVP document
        update_srvp_document(req_statuses)
        print("\nProcess completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())