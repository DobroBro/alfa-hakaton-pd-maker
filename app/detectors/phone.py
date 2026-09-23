import re

from app.types import PRIORITY, Span

_RUN_RE = re.compile(r"\+?[0-9][0-9 ()-]*")

_PASSPORT_FORM1 = re.compile(r"\d{2}\s?\d{2}\s?\d{6}")
_PASSPORT_FORM2 = re.compile(r"\d{4}\s?\d{6}")


def _is_passport_form(raw: str, digits: str) -> bool:
    if " " not in raw:
        return False
    if len(digits) != 10:
        return False
    return bool(_PASSPORT_FORM1.fullmatch(raw)) or bool(_PASSPORT_FORM2.fullmatch(raw))


def _is_phone(raw: str, digits: str) -> bool:
    if len(digits) not in (10, 11):
        return False
    if _is_passport_form(raw, digits):
        return False
    if len(digits) == 11 and digits[0] in "78":
        return True
    if len(digits) == 10 and digits[0] == "9":
        return True
    return len(digits) == 10 and any(ch in raw for ch in " -()")


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
            for cnt in (11, 10):
                j = i + cnt
                if j <= n:
                    d1 = dpos[j - 1]
                    if d1 - d0 + 1 <= 30:
                        raw = text[d0:d1 + 1]
                        digits = "".join(text[p] for p in dpos[i:j])
                        if _is_phone(raw, digits) and _bounded(text, d0, d1 + 1):
                            spans.append(Span(d0, d1 + 1, "phone", PRIORITY["phone"]))
                            i = j
                            found = True
                            break
            if not found:
                i += 1
    return spans