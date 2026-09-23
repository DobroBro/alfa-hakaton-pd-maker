import re

from app.settings import RULES
from app.types import PRIORITY, Span

_MARKERS = [(m["marker"], m["type"]) for m in RULES.get("document_markers", [])]

_DATE_RE = re.compile(r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}[./-]\d{1,2}[./-]\d{1,2}")


def find(text: str) -> list[Span]:
    folded = text.casefold().replace("ё", "е")
    spans = []
    for marker, ptype in _MARKERS:
        idx = folded.find(marker)
        while idx != -1:
            left_ok = idx == 0 or not folded[idx - 1].isalpha()
            right_ok = idx + len(marker) >= len(folded) or not folded[idx + len(marker)].isalpha()
            if left_ok and right_ok:
                start = idx
                pos = idx + len(marker)
                while pos < len(text) and text[pos] in " \t:":
                    pos += 1
                value_start = pos
                while pos < len(text) and text[pos] not in ",;\n":
                    if text[pos].isdigit() and _DATE_RE.match(text, pos):
                        break
                    pos += 1
                value_end = pos
                value = text[value_start:value_end]
                if value and len(value) <= 120:
                    spans.append(Span(start, value_end, ptype, PRIORITY[ptype]))
            idx = folded.find(marker, idx + 1)
    return spans