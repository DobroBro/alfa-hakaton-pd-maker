import re

from app.context import has_keyword
from app.types import PRIORITY, Span

_INN_RE = re.compile(r"(?<!\d)(?:\d{12}|\d{10})(?!\d)")


def inn10_ok(n: str) -> bool:
    coef = (2, 4, 10, 3, 5, 9, 4, 6, 8)
    check = sum(int(n[i]) * coef[i] for i in range(9)) % 11 % 10
    return check == int(n[9])


def inn12_ok(n: str) -> bool:
    c1 = (7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
    c2 = (3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
    a = sum(int(n[i]) * c1[i] for i in range(10)) % 11 % 10
    b = sum(int(n[i]) * c2[i] for i in range(11)) % 11 % 10
    return a == int(n[10]) and b == int(n[11])


def find(text: str) -> list[Span]:
    folded = text.casefold().replace("ё", "е")
    spans = []
    for m in _INN_RE.finditer(text):
        n = m.group()
        if len(n) == 12:
            if inn12_ok(n):
                spans.append(Span(m.start(), m.end(), "inn", PRIORITY["inn"]))
        else:
            if inn10_ok(n) and has_keyword(folded, m.start(), m.end(), ("инн",), 40):
                spans.append(Span(m.start(), m.end(), "inn", PRIORITY["inn"]))
    return spans