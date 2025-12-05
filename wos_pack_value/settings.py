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
SCREENSHOTS_DIR = DATA_RAW_DIR / "screenshots"
DATA_REVIEW_DIR = PROJECT_ROOT / "data_review"

DEFAULT_CONFIG_PATH = CONFIG_DIR / "item_values.yaml"
DEFAULT_PROCESSED_PACKS = DATA_PROCESSED_DIR / "packs.json"
DEFAULT_PROCESSED_ITEMS = DATA_PROCESSED_DIR / "items.json"
DEFAULT_PROCESSED_VALUATIONS = DATA_PROCESSED_DIR / "valuations.json"
DEFAULT_SITE_PACKS = SITE_DATA_DIR / "packs.json"
DEFAULT_SITE_ITEMS = SITE_DATA_DIR / "items.json"
DEFAULT_SITE_REFERENCES = SITE_DATA_DIR / "reference_packs.json"
DEFAULT_INGESTION_CONFIG_PATH = CONFIG_DIR / "ingestion.yaml"
DEFAULT_ANALYSIS_CONFIG_PATH = CONFIG_DIR / "analysis.yaml"
DEFAULT_PLAYER_PROFILES_PATH = CONFIG_DIR / "player_profiles.yaml"
DEFAULT_SITE_ANALYSIS_OVERALL = SITE_DATA_DIR / "pack_ranking_overall.json"
DEFAULT_SITE_ANALYSIS_BY_CATEGORY = SITE_DATA_DIR / "pack_ranking_by_category.json"
DEFAULT_SITE_ANALYSIS_PROFILE = "pack_ranking_profile_{profile}.json"
DEFAULT_SITE_VALIDATION_REPORT = SITE_DATA_DIR / "validation_report.json"
DEFAULT_VALIDATION_CONFIG_PATH = CONFIG_DIR / "validation.yaml"
DEFAULT_OCR_REVIEW_RAW = DATA_REVIEW_DIR / "ocr_packs_raw.json"
DEFAULT_OCR_REVIEWED = DATA_REVIEW_DIR / "ocr_packs_reviewed.json"
