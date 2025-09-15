import json
import re
import subprocess
from pathlib import Path

# Define paths
ROOT_DIR = Path(__file__).parent.parent
SRVP_PATH = ROOT_DIR / "resources" / "docs" / "srvp.md"
OUTPUT_PATH = ROOT_DIR / "resources" / "docs" / "srvp_con_resultados.md"
REPORT_PATH = ROOT_DIR / "report.json"
TESTS_DIR = ROOT_DIR / "tests"

REQ_FUNC_PATTERN = r"Covers: ([\s\S]*?)(?:\n\n|\Z)"
REQ_ID_PATTERN = r"REQ-FUNC-\w+-\d{3}"


def run_tests():
    """Run pytest and generate a JSON report."""
    print("Running tests...")
    subprocess.run(
        [
            "pytest",
            f"--json-report",
            f"--json-report-file={REPORT_PATH}",
            str(TESTS_DIR),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    print(f"Test report generated at {REPORT_PATH}")


def parse_test_report():
    """Parse the JSON test report to get test outcomes."""
    print("Parsing test report...")
    if not REPORT_PATH.exists():
        raise FileNotFoundError(f"Test report not found at {REPORT_PATH}")

    with open(REPORT_PATH, "r") as f:
        report = json.load(f)

    test_outcomes = {}
    for test in report.get("tests", []):
        test_outcomes[test["nodeid"]] = test["outcome"]
    return test_outcomes


def extract_req_ids_from_docstrings():
    """Extract requirement IDs from test function docstrings."""
    print("Extracting requirement IDs from test files...")
    req_to_tests = {}
    for test_file in TESTS_DIR.glob("test_*.py"):
        content = test_file.read_text()
        # This is a simplified parser. It assumes 'def test_...' starts a test.
        for match in re.finditer(r"def (test_\w+)\([^)]*\):\s+\"\"\"([\s\S]*?)\"\"\"", content):
            test_name = match.group(1)
            docstring = match.group(2)
            # Full nodeid format is 'tests/test_file.py::test_function_name'
            full_test_name = f"tests/{test_file.name}::{test_name}"

            # Find all REQ-FUNC IDs in the docstring
            covered_reqs = re.findall(r"REQ-FUNC-\w+-\d{3}", docstring)
            for req_id in covered_reqs:
                if req_id not in req_to_tests:
                    req_to_tests[req_id] = []
                req_to_tests[req_id].append(full_test_name)

    return req_to_tests


def get_requirement_statuses(test_outcomes, req_to_tests):
    """Determine the status of each requirement based on test outcomes."""
    print("Determining requirement statuses...")
    req_statuses = {}
    for req_id, test_names in req_to_tests.items():
        outcomes = [test_outcomes.get(name, "skipped") for name in test_names]
        # A requirement is 'Failed' if any of its tests fail.
        if "failed" in outcomes:
            req_statuses[req_id] = "Failed"
        # It is 'Verified' only if all of its tests pass.
        elif outcomes and all(o == "passed" for o in outcomes):
            req_statuses[req_id] = "Verified"
        # Otherwise, the status is not determined and the markdown will not be updated for this req.
    return req_statuses


def update_srvp_document(req_statuses):
    """Update the SRVP document with the new requirement statuses."""
    print(f"Updating SRVP document: {SRVP_PATH}")
    content = SRVP_PATH.read_text()

    lines = content.split("\n")
    new_lines = []

    # Regex to find a markdown table row for a functional requirement
    # It captures the ID and the status part of the line
    req_line_pattern = re.compile(r"\| (REQ-FUNC-\w+-\d{3}) \| Test \|.*?\| (\[ \] Not Started|Verified|Failed) \|")

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
            else:
                new_lines.append(line) # Keep line as is if no status found
        else:
            new_lines.append(line)

    OUTPUT_PATH.write_text("\n".join(new_lines))
    print(f"SRVP document updated and saved to {OUTPUT_PATH}")


def main():
    """Main function to run the entire process."""
    try:
        run_tests()
        test_outcomes = parse_test_report()
        req_to_tests = extract_req_ids_from_docstrings()
        req_statuses = get_requirement_statuses(test_outcomes, req_to_tests)
        update_srvp_document(req_statuses)
        print("\nProcess completed successfully!")
    except (subprocess.CalledProcessError, FileNotFoundError, KeyError) as e:
        print(f"\nAn error occurred: {e}")
        if isinstance(e, subprocess.CalledProcessError):
            print("----- pytest stdout -----")
            print(e.stdout)
            print("----- pytest stderr -----")
            print(e.stderr)


if __name__ == "__main__":
    main()
