import re

from app.context import has_keyword
from app.types import PRIORITY, Span

_DEPT_RE = re.compile(r"\b\d{3}-\d{3}\b")
_KEYS = ("код подразделения", "к/п")


def find(text: str) -> list[Span]:
    folded = text.casefold().replace("ё", "е")
    spans = []
    for m in _DEPT_RE.finditer(text):
        if has_keyword(folded, m.start(), m.end(), _KEYS, 40):
            spans.append(Span(m.start(), m.end(), "department_code", PRIORITY["department_code"]))
    return spans