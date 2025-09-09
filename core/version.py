from importlib import resources

__all__ = ["__version__"]


def _load_version() -> str:
    try:
        with resources.files("resources").joinpath("version_info.txt").open("r", encoding="utf-8") as f:  # type: ignore[attr-defined]
            return f.read().strip()
    except Exception:
        return "0.0.0"

__version__ = _load_version()
