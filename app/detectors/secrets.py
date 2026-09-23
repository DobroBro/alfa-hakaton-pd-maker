import re

from app.context import has_keyword
from app.types import PRIORITY, Span

_CVV_KEYS = ("cvv", "cvc", "cvv2", "cvc2", "код безопасности")
_PIN_KEYS = ("пин-код", "пинкод", "пин", "pin")

_CVV3_RE = re.compile(r"(?<!\d)\d{3}(?!\d)")
_CVV4_RE = re.compile(r"(?<!\d)\d{4}(?!\d)")
_PIN_RE = re.compile(r"(?<!\d)\d{4}(?!\d)")


def find(text: str) -> list[Span]:
    folded = text.casefold().replace("ё", "е")
    spans = []
    for m in _CVV3_RE.finditer(text):
        if has_keyword(folded, m.start(), m.end(), _CVV_KEYS, 30):
            spans.append(Span(m.start(), m.end(), "cvv", PRIORITY["cvv"]))
    for m in _CVV4_RE.finditer(text):
        if has_keyword(folded, m.start(), m.end(), _CVV_KEYS, 30) and has_keyword(
            folded, m.start(), m.end(), ("amex",), 30
        ):
            spans.append(Span(m.start(), m.end(), "cvv", PRIORITY["cvv"]))
    for m in _PIN_RE.finditer(text):
        if has_keyword(folded, m.start(), m.end(), _PIN_KEYS, 30):
            spans.append(Span(m.start(), m.end(), "pin", PRIORITY["pin"]))
    return spans