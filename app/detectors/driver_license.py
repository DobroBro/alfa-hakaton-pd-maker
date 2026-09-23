import re

from app.context import closest_key_end, has_keyword, has_keyword_prefix
from app.types import PRIORITY, Span

_WORD = r"(?:\b(?:серия|номер)\b|№)"

_DRIVER_RE = re.compile(
    rf"(?<!\d)(?:"
    rf"(?:{_WORD}\s*)?\d{{2}}\s*(?:{_WORD}\s*)?\d{{2}}\s*(?:{_WORD}\s*)?\d{{6}}"
    rf"|"
    rf"(?:{_WORD}\s*)?\d{{4}}\s*(?:{_WORD}\s*)?\d{{6}}"
    rf")(?!\d)"
)

_DRIVER_KEYS = ("водительск", "в/у", "ву №")
_PASSPORT_KEYS = ("паспорт",)


def find(text: str) -> list[Span]:
    folded = text.casefold().replace("ё", "е")
    spans = []
    for m in _DRIVER_RE.finditer(text):
        start, end = m.start(), m.end()
        has_driver = has_keyword_prefix(folded, start, end, _DRIVER_KEYS, 40)
        if not has_driver:
            continue
        has_passport = has_keyword(folded, start, end, _PASSPORT_KEYS, 40)
        if has_passport:
            d_end = closest_key_end(folded, start, end, _DRIVER_KEYS, 40)
            p_end = closest_key_end(folded, start, end, _PASSPORT_KEYS, 40)
            if p_end is not None and (d_end is None or p_end <= d_end):
                continue
        spans.append(Span(start, end, "driver_license", PRIORITY["driver_license"]))
    return spans