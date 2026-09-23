import re

from app.context import has_keyword
from app.types import PRIORITY, Span

_FP_RE = re.compile(r"(?<!\d)\d{2}\s?\d{7}(?!\d)")
_KEYS = ("загранпаспорт", "заграничный паспорт")


def find(text: str) -> list[Span]:
    folded = text.casefold().replace("ё", "е")
    spans = []
    for m in _FP_RE.finditer(text):
        if has_keyword(folded, m.start(), m.end(), _KEYS, 40):
            spans.append(Span(m.start(), m.end(), "foreign_passport", PRIORITY["foreign_passport"]))
    return spans