import re

from app.types import PRIORITY, Span

_RUN_RE = re.compile(r"[0-9][0-9 \-]*")


def luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _is_card(raw: str) -> bool:
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) < 13 or len(digits) > 19:
        return False
    if not luhn_ok(digits):
        return False
    if any(ch in raw for ch in " -"):
        groups = re.split(r"[ \-]+", raw)
        if not all(len(g) == 4 for g in groups):
            return False
    return True


def _bounded(text: str, i: int, k: int) -> bool:
    left_ok = i == 0 or not text[i - 1].isdigit()
    right_ok = k >= len(text) or not text[k].isdigit()
    return left_ok and right_ok


def find(text: str) -> list[Span]:
    spans = []
    for m in _RUN_RE.finditer(text):
        start, end = m.start(), m.end()
        run = text[start:end]
        if len(run) > 19 and all(ch.isdigit() for ch in run):
            continue
        i = start
        while i < end:
            if not text[i].isdigit():
                i += 1
                continue
            found = False
            for k in range(min(end, i + 35), i, -1):
                if _is_card(text[i:k]) and _bounded(text, i, k):
                    spans.append(Span(i, k, "card_number", PRIORITY["card_number"]))
                    i = k
                    found = True
                    break
            if not found:
                i += 1
    return spans