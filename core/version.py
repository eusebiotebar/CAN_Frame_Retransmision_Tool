from importlib import resources

__all__ = ["__version__"]


def _load_version() -> str:
    try:
                # Construimos la ruta en pasos para mantener las líneas cortas (E501)
                res_root = resources.files("resources")  # type: ignore[attr-defined]
                version_path = res_root.joinpath("version_info.txt")
                with version_path.open(encoding="utf-8") as f:
                        return f.read().strip()
    except Exception:
        return "0.0.0"

__version__ = _load_version()

