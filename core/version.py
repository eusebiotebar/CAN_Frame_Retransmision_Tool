from importlib import resources

__all__ = ["__version__"]


def _load_version() -> str:
    try:
        # Build path in separate variable to keep line length within lint limits
        version_path = resources.files("resources").joinpath("version_info.txt")  # type: ignore[attr-defined]
        with version_path.open(encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "0.0.0"

__version__ = _load_version()

# Ajuste: se refactorizó para cumplir con reglas de lint (E501) y se añade este comentario para asegurar commit.
