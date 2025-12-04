"""Project-wide paths and defaults."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_RAW_DIR = PROJECT_ROOT / "data_raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data_processed"
IMAGES_RAW_DIR = PROJECT_ROOT / "images_raw"
IMAGES_PROCESSED_DIR = PROJECT_ROOT / "images_processed"
SITE_DATA_DIR = PROJECT_ROOT / "site_data"
LOG_DIR = PROJECT_ROOT / "logs"

DEFAULT_CONFIG_PATH = CONFIG_DIR / "item_values.yaml"
DEFAULT_PROCESSED_PACKS = DATA_PROCESSED_DIR / "packs.json"
DEFAULT_PROCESSED_ITEMS = DATA_PROCESSED_DIR / "items.json"
DEFAULT_PROCESSED_VALUATIONS = DATA_PROCESSED_DIR / "valuations.json"
DEFAULT_SITE_PACKS = SITE_DATA_DIR / "packs.json"
DEFAULT_SITE_ITEMS = SITE_DATA_DIR / "items.json"
