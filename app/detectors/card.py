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


def _is_card(raw: str, digits: str) -> bool:
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
        dpos = [i for i in range(start, end) if text[i].isdigit()]
        n = len(dpos)
        i = 0
        while i < n:
            d0 = dpos[i]
            found = False
            for cnt in range(19, 12, -1):
                j = i + cnt
                if j <= n:
                    d1 = dpos[j - 1]
                    if d1 - d0 + 1 <= 35:
                        raw = text[d0:d1 + 1]
                        digits = "".join(text[p] for p in dpos[i:j])
                        if _is_card(raw, digits) and _bounded(text, d0, d1 + 1):
                            spans.append(
                                Span(d0, d1 + 1, "card_number", PRIORITY["card_number"])
                            )
                            i = j
                            found = True
                            break
            if not found:
                i += 1
    return spans