import re

from app.context import has_keyword
from app.types import PRIORITY, Span

_WORD = r"(?:\b(?:серия|номер)\b|№)"

_PASSPORT_RE = re.compile(
    r"(?<!\d)(?:"
    r"(?:{w}\s*)?\d{{2}}\s*(?:{w}\s*)?\d{{2}}\s*(?:{w}\s*)?\d{{6}}"
    r"|"
    r"(?:{w}\s*)?\d{{4}}\s*(?:{w}\s*)?\d{{6}}"
    r")(?!\d)".format(w=_WORD)
)


def find(text: str) -> list[Span]:
    folded = text.casefold().replace("ё", "е")
    spans = []
    for m in _PASSPORT_RE.finditer(text):
        start, end = m.start(), m.end()
        has_passport = has_keyword(folded, start, end, ("паспорт",), 40)
        has_series = has_keyword(folded, start, end, ("серия",), 40)
        has_number = has_keyword(folded, start, end, ("номер",), 40)
        if has_passport or (has_series and has_number):
            spans.append(Span(start, end, "passport", PRIORITY["passport"]))
    return spans