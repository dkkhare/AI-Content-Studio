"""
Global application constants.
"""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT_DIR / "data"

INPUT_DIR = ROOT_DIR / "input"

OUTPUT_DIR = ROOT_DIR / "output"

TEMP_DIR = ROOT_DIR / "temp"

MODELS_DIR = ROOT_DIR / "models"

LOGS_DIR = ROOT_DIR / "logs"

CONFIG_DIR = ROOT_DIR / "backend" / "config"

DEFAULT_THEME = "dark"

DATABASE_NAME = "studio.db"