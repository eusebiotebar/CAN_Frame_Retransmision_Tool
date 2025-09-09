import pytest


@pytest.fixture
def sample_frame():
    return {"id": 0x100, "data": bytes([1,2,3])}
