from pathlib import Path

from setuptools import find_packages, setup

ROOT = Path(__file__).parent
version = (ROOT / "resources" / "version_info.txt").read_text(encoding="utf-8").strip()

setup(
    name="CAN_Frame_Retransmision_Tool",
    version=version,
    description="CAN Frame Retransmission Tool",
    author="Your Name",
    packages=find_packages(exclude=("tests", "resources", "scripts", "hooks")),
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=[],
    extras_require={
        "dev": ["pytest", "black", "mypy", "ruff"],
    },
    entry_points={
        "console_scripts": [
            "can-retransmit=core.main:main",
        ]
    },
)
