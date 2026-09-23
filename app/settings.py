import os
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"

STORE = os.environ.get("STORE", "memory")
REDIS_URL = os.environ.get("REDIS_URL", "")
PD_STORE_KEY = os.environ.get("PD_STORE_KEY", "")
MAX_IN_FLIGHT = int(os.environ.get("MAX_IN_FLIGHT", "512"))
STORE_TTL_SECONDS = 1800


def load_systems() -> dict:
    with open(CONFIG_DIR / "systems.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_gazetteer() -> dict:
    with open(CONFIG_DIR / "gazetteer.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_rules() -> dict:
    with open(CONFIG_DIR / "rules.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


SYSTEMS_CONFIG = load_systems()
GAZETTEER = load_gazetteer()
RULES = load_rules()
DEFAULT_SYSTEM = SYSTEMS_CONFIG["default_system"]
STORE_TTL_SECONDS = SYSTEMS_CONFIG.get("store_ttl_seconds", STORE_TTL_SECONDS)
MAX_IN_FLIGHT = int(os.environ.get("MAX_IN_FLIGHT", SYSTEMS_CONFIG.get("max_in_flight", 512)))