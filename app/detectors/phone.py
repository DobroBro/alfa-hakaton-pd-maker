import re

from app.types import PRIORITY, Span

_RUN_RE = re.compile(r"\+?[0-9][0-9 ()-]*")

_PASSPORT_FORM1 = re.compile(r"\d{2}\s?\d{2}\s?\d{6}")
_PASSPORT_FORM2 = re.compile(r"\d{4}\s?\d{6}")


def _clean(raw: str) -> str:
    return "".join(ch for ch in raw if ch.isdigit())


def _is_passport_form(raw: str) -> bool:
    if " " not in raw:
        return False
    digits = _clean(raw)
    if len(digits) != 10:
        return False
    return bool(_PASSPORT_FORM1.fullmatch(raw)) or bool(_PASSPORT_FORM2.fullmatch(raw))


def _is_phone(raw: str) -> bool:
    digits = _clean(raw)
    if len(digits) not in (10, 11):
        return False
    if _is_passport_form(raw):
        return False
    if len(digits) == 11 and digits[0] in "78":
        return True
    if len(digits) == 10 and digits[0] == "9":
        return True
    if len(digits) == 10 and any(ch in raw for ch in " -()"):
        return True
    return False


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
            for k in range(min(end, i + 30), i, -1):
                if _is_phone(text[i:k]) and _bounded(text, i, k):
                    spans.append(Span(i, k, "phone", PRIORITY["phone"]))
                    i = k
                    found = True
                    break
            if not found:
                i += 1
    return spans