from importlib import resources

__all__ = ["__version__"]


def _load_version() -> str:
    """Load version string from the version file.

    Returns "0.0.0" if any exception occurs (safe fallback).
    """
    try:
        res_root = resources.files("core")  # type: ignore[attr-defined]
        version_path = res_root.joinpath("version_info.txt")
        with version_path.open(encoding="utf-8") as fh:
            return fh.read().strip()
    except Exception:  # noqa: BLE001 broad fallback is intentional
        return "0.0.0"


__version__ = _load_version()
