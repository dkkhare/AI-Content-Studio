"""
Filesystem helper functions.
"""

from pathlib import Path

from backend.core.constants import (
    DATA_DIR,
    INPUT_DIR,
    OUTPUT_DIR,
    TEMP_DIR,
    MODELS_DIR,
    LOGS_DIR,
)


def ensure_directories() -> None:
    """
    Create all required folders.
    """

    folders = [
        DATA_DIR,
        INPUT_DIR,
        OUTPUT_DIR,
        TEMP_DIR,
        MODELS_DIR,
        LOGS_DIR,
    ]

    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)