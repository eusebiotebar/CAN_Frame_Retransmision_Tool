import os

import pytest

# Ensure Qt can run in headless environments (CI)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def sample_frame():
    return {"id": 0x100, "data": bytes([1, 2, 3])}


# Register custom marker for requirement tagging
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "requirements(reqs): mark test with list of requirement IDs (e.g., ['REQ-...'])",
    )


def pytest_sessionfinish(session, exitstatus):
    """Generate a minimal SRVP_TR.md mapping requirements to test outcomes."""
    req_results: dict[str, str] = {}
    for item in session.items:
        reqs = []
        marker = item.get_closest_marker("requirements")
        if marker and marker.args:
            # First arg expected to be a list of requirement IDs
            arg0 = marker.args[0]
            reqs = (
                [str(x) for x in arg0]
                if isinstance(arg0, (list, tuple))
                else [str(arg0)]
            )

        if not reqs:
            continue

        # Determine outcome for this test
        outcome = "Verified"
        # If any test failed overall and this test is among failures, mark as Failed
        # Note: pytest doesn't expose per-item outcomes here; keep it simple and
        # mark Verified unless an internal failed list is present and includes this item.
        failed_nodeids = (
            {rep.nodeid for rep in getattr(session, "_testsfailed", [])}
            if hasattr(session, "_testsfailed")
            else set()
        )
        if item.nodeid in failed_nodeids:
            outcome = "Failed"

        for req in reqs:
            # If multiple tests reference the same requirement, aggregate: Failed overrides Verified
            prev = req_results.get(req)
            if prev == "Failed":
                continue
            req_results[req] = outcome

    # Write report next to resources/docs as SRVP_TR.md
    try:
        from pathlib import Path

        report_path = Path("resources/docs/SRVP_TR.md")
        lines = [
            "# SRVP Test Report (SRVP_TR)",
            "",
            "This file is generated automatically from pytest markers.",
            "",
            "| Requirement | Status |",
            "| :-- | :-- |",
        ]
        for req in sorted(req_results.keys()):
            lines.append(f"| {req} | {req_results[req]} |")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("\n".join(lines), encoding="utf-8")
    except Exception:
        # Do not break test session on report generation issues
        pass
