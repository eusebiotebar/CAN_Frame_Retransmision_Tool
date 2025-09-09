from core.main import get_version


def test_version_format():
    v = get_version()
    assert isinstance(v, str)
    assert v
    assert v.count('.') >= 1
