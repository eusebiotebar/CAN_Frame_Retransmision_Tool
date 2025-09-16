#!/usr/bin/env python3
"""
Update SRVP Document with Test Results
====================================

This script runs pytest tests and updates the SRVP document with test verification results.

Enhancements:
- Generates a standalone SRVP Test Report (srvp_TR.md) with a YAML front matter including
    docType, docSubtitle, docVersion, docAuthor, and createdDate derived from release metadata.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
SRVP_PATH = ROOT_DIR / "resources" / "docs" / "srvp.md"
OUTPUT_PATH = ROOT_DIR / "resources" / "docs" / "srvp_TR.md"
REPORT_PATH = ROOT_DIR / "resources" / "docs" / "report.json"
TESTS_DIR = ROOT_DIR / "tests"
SRS_PATH = ROOT_DIR / "resources" / "docs" / "srs.md"


def check_pytest_available():
    """Check if pytest is available."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
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
                sys.executable,
                "-m",
                "pytest",  # Use sys.executable to ensure correct Python
                "--json-report",
                f"--json-report-file={REPORT_PATH}",
                str(TESTS_DIR),
                "-v",  # Verbose output for debugging
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"Test report generated at {REPORT_PATH}")
        print(f"pytest stdout: {result.stdout}")
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

    with open(REPORT_PATH, encoding="utf-8") as f:
        report = json.load(f)

    test_outcomes = {}
    for test in report.get("tests", []):
        test_outcomes[test["nodeid"]] = test["outcome"]

    print(f"Found {len(test_outcomes)} test results")
    return test_outcomes


def extract_requirement_ids_from_docs() -> set[str]:
    """Extract all requirement IDs appearing in SRVP/SRS documents.

    Matches patterns like REQ-FUNC-LOG-010, REQ-NFR-REL-001, etc.
    """
    ids: set[str] = set()
    pattern = re.compile(r"REQ-(?:[A-Z]+-)+\d{3}")
    for path in (SRVP_PATH, SRS_PATH):
        try:
            if path.exists():
                text = path.read_text(encoding="utf-8")
                ids.update(pattern.findall(text))
        except Exception:
            # Ignore read errors; best-effort extraction
            pass
    return ids


def _read_doc_author_from_srvp() -> str | None:
    """Best-effort extraction of docAuthor from SRVP front matter as fallback."""
    try:
        if SRVP_PATH.exists():
            txt = SRVP_PATH.read_text(encoding="utf-8")
            m = re.search(r"^docAuthor:\s*(.+)$", txt, flags=re.MULTILINE)
            if m:
                return m.group(1).strip()
    except Exception:
        pass
    return None


def _git_cmd_output(args: list[str]) -> str | None:
    try:
        out = subprocess.check_output(["git", *args], cwd=ROOT_DIR, text=True).strip()
        return out
    except Exception:
        return None


def _get_release_metadata() -> tuple[str, str, str]:
    """Return (version, author, date) for the report front matter.

        Strategy:
        - version: core.version.__version__ (from version_info.txt), fallback "0.0.0"
        - author: env RELEASE_AUTHOR or GITHUB_ACTOR, then SRVP docAuthor,
            then git user.name, else "Unknown"
        - date: env RELEASE_DATE (YYYY-MM-DD), then latest commit author-date,
            else today in YYYY-MM-DD
    """
    # Version
    try:
        from core.version import __version__ as ver
    except Exception:
        ver = "0.0.0"

    # Author
    author = (
        os.environ.get("RELEASE_AUTHOR")
        or os.environ.get("GITHUB_ACTOR")
        or _read_doc_author_from_srvp()
        or _git_cmd_output(["config", "user.name"])  # local git user
        or "Unknown"
    )

    # Date
    date = os.environ.get("RELEASE_DATE")
    if not date:
        # Try latest commit author date (ISO 8601); convert to YYYY-MM-DD
        iso = _git_cmd_output(["log", "-1", "--format=%aI"])  # e.g., 2025-09-16T09:58:12+00:00
        if iso:
            try:
                date = datetime.fromisoformat(iso.replace("Z", "+00:00")).date().isoformat()
            except Exception:
                date = None
    if not date:
        date = datetime.now().date().isoformat()

    return ver, author, date


def extract_req_ids_from_docstrings():
    """Extract requirement IDs from test function docstrings."""
    print("Extracting requirement IDs from test files...")
    req_to_tests = {}

    for test_file in TESTS_DIR.glob("test_*.py"):
        print(f"  Processing {test_file.name}...")
        content = test_file.read_text(encoding="utf-8")

        # IMPROVED REGEX: More flexible whitespace handling
        # Allows for any amount of whitespace and newlines between function def and docstring
        pattern = r'def (test_\w+)\([^)]*\):[\s\S]*?"""([\s\S]*?)"""'

        for match in re.finditer(pattern, content):
            test_name = match.group(1)
            docstring = match.group(2)
            # Full nodeid format to match pytest output
            full_test_name = f"tests/{test_file.name}::{test_name}"

            # Find requirement IDs in the docstring (support FUNC, NFR, etc.)
            req_ids = re.findall(r"REQ-(?:[A-Z]+-)+\d{3}", docstring)
            for req_id in req_ids:
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
            req_statuses[req_id] = "[x] Failed"
        # It is 'Verified' only if all of its tests pass.
        elif outcomes and all(o == "passed" for o in outcomes):
            req_statuses[req_id] = "[x] Verified"
        # Otherwise, the status is not determined
        else:
            print(f"    No clear status for {req_id} (outcomes: {outcomes})")

    print(f"Determined status for {len(req_statuses)} requirements")
    return req_statuses


def build_markdown_report(
    req_statuses: dict[str, str],
    req_to_tests: dict[str, list[str]],
    test_outcomes: dict[str, str],
) -> str:
    """Create a standalone Markdown report summarizing test results vs requirements."""
    total_tests = len(test_outcomes)
    passed = sum(1 for o in test_outcomes.values() if o == "passed")
    failed = sum(1 for o in test_outcomes.values() if o == "failed")
    skipped = sum(1 for o in test_outcomes.values() if o == "skipped")

    # Aggregate requirement IDs from docs and tests
    ids_from_docs = extract_requirement_ids_from_docs()
    all_req_ids_sorted = sorted(set(req_to_tests.keys()) | ids_from_docs)

    # Compute counts across all requirements (default Not Started)
    def status_of(req_id: str) -> str:
        return req_statuses.get(req_id, "[ ] Not Started")

    total_reqs = len(all_req_ids_sorted)
    verified = sum(1 for rid in all_req_ids_sorted if status_of(rid).endswith("Verified"))
    req_failed = sum(1 for rid in all_req_ids_sorted if status_of(rid).endswith("Failed"))
    pending = total_reqs - verified - req_failed

    # Front matter with release metadata
    version, author, date = _get_release_metadata()

    lines: list[str] = []
    lines.append("---")
    lines.append("docType: Software Requirements Verification Plan Report (SRVPR)")
    lines.append("docSubtitle: CAN Frame Retransmission Tool")
    lines.append(f"docVersion: {version}")
    lines.append(f"docAuthor: {author}")
    lines.append(f"createdDate: {date}")
    lines.append("---")
    lines.append("")
    lines.append("# Test Report - SRVP Functional Requirements")
    lines.append("")
    lines.append(
        "This document summarizes the latest test run and the verification status "
        "of the SRVP functional requirements."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(
        f"- Tests: {passed} passed, {failed} failed, {skipped} skipped (total {total_tests})"
    )
    lines.append(
        f"- Requirements: {verified} verified, {req_failed} failed, {pending} pending "
        f"(total {total_reqs})"
    )
    lines.append("")

    # Requirements table
    lines.append("## Requirements Status")
    lines.append("")
    lines.append("| Requirement | Status | Tests |")
    lines.append("| --- | --- | --- |")
    # Determine the full set of requirement IDs from SRVP document + tests mapping
    # Use precomputed comprehensive list
    all_req_ids = all_req_ids_sorted

    for req_id in all_req_ids:
        status = req_statuses.get(req_id, "[ ] Not Started")
        tests = ", ".join(req_to_tests.get(req_id, []))
        lines.append(f"| {req_id} | {status} | {tests} |")
    lines.append("")

    # Detailed section
    lines.append("## Details")
    lines.append("")
    for req_id in all_req_ids:
        lines.append(f"### {req_id}")
        lines.append("")
        lines.append(f"- Status: {req_statuses.get(req_id, '[ ] Not Started')}")
        lines.append("- Tests:")
        for nodeid in req_to_tests.get(req_id, []):
            outcome = test_outcomes.get(nodeid, "skipped")
            badge = "✅" if outcome == "passed" else ("❌" if outcome == "failed" else "➖")
            lines.append(f"  - {badge} `{nodeid}` — {outcome}")
        if not req_to_tests.get(req_id):
            lines.append("  - ➖ No tests mapped yet")
        lines.append("")

    return "\n".join(lines)


def write_markdown_report(
    req_statuses: dict[str, str],
    req_to_tests: dict[str, list[str]],
    test_outcomes: dict[str, str],
) -> None:
    """Write the standalone Markdown report to OUTPUT_PATH."""
    report = build_markdown_report(req_statuses, req_to_tests, test_outcomes)
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(f"Test report written to {OUTPUT_PATH}")


def main():
    """Main function to run the entire process."""
    print("=== CAN Frame Retransmission Tool - SRVP Update Script ===")

    # Check prerequisites
    if not check_pytest_available():
        return 1

    if not SRVP_PATH.exists():
        print(f"WARNING: SRVP file not found: {SRVP_PATH} (continuing without it)")

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
        print(f"  ... and {len(test_outcomes) - 5} more")

        # Step 3: Extract requirement IDs from test docstrings
        req_to_tests = extract_req_ids_from_docstrings()
        print("\n--- DEBUG: REQ TO TESTS MAPPING ---")
        for req_id, tests in list(req_to_tests.items())[:5]:  # Show first 5
            print(f"  {req_id}: {tests}")
        print(f"  ... and {len(req_to_tests) - 5} more")

        # Step 4: Determine requirement statuses
        req_statuses = get_requirement_statuses(test_outcomes, req_to_tests)
        print("\n--- DEBUG: FINAL REQ STATUSES ---")
        for req_id, status in req_statuses.items():
            print(f"  {req_id}: {status}")

        # Step 5: Generate standalone Markdown test report
        write_markdown_report(req_statuses, req_to_tests, test_outcomes)
        print("\nProcess completed successfully!")
        return 0

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())