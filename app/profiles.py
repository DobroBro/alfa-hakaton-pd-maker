from dataclasses import dataclass, field

from app.settings import SYSTEMS_CONFIG
from app.types import PRIORITY

ALL_TYPES = set(PRIORITY.keys()) - {"date_candidate"}

_ALLOWED_STYLES = {"reference", "token"}


@dataclass(frozen=True)
class Profile:
    name: str
    enabled: bool
    demask_enabled: bool
    mask_style: str
    combo_rules: bool
    types: frozenset = field(default_factory=frozenset)


def _load_types(raw) -> frozenset:
    if raw == "all":
        return frozenset(ALL_TYPES)
    return frozenset(raw)


def load_profiles() -> dict[str, Profile]:
    profiles = {}
    for name, cfg in SYSTEMS_CONFIG["systems"].items():
        style = cfg.get("mask_style", "reference")
        if style not in _ALLOWED_STYLES:
            raise RuntimeError(f"unsupported mask_style: {style}")
        profiles[name] = Profile(
            name=name,
            enabled=cfg.get("enabled", True),
            demask_enabled=cfg.get("demask_enabled", False),
            mask_style=style,
            combo_rules=cfg.get("combo_rules", False),
            types=_load_types(cfg.get("types", [])),
        )
    return profiles