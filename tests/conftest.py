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
