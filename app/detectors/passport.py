import re

from app.context import has_keyword
from app.settings import RULES
from app.types import PRIORITY, Span

_SERIES_WORDS = tuple(RULES.get("series_number_words", []))
_LETTER_SERIES = tuple(w for w in _SERIES_WORDS if w != "№")
_WORD_WORDS = list(_LETTER_SERIES)
_WORD = r"(?:\b(?:" + "|".join(_WORD_WORDS) + r")\b|№)"

_PASSPORT_RE = re.compile(
    rf"(?<!\d)(?:"
    rf"(?:{_WORD}\s*)?\d{{2}}\s*(?:{_WORD}\s*)?\d{{2}}\s*(?:{_WORD}\s*)?\d{{6}}"
    rf"|"
    rf"(?:{_WORD}\s*)?\d{{4}}\s*(?:{_WORD}\s*)?\d{{6}}"
    rf")(?!\d)"
)

_PASSPORT_KEYS = tuple(RULES.get("passport_keys", []))
_FOREIGN_PREFIXES = ("заграничный", "загран")


def _is_phone(digits: str) -> bool:
    if len(digits) == 11 and digits[0] in "78":
        return True
    return len(digits) == 10 and digits[0] == "9"


def _has_foreign_prefix(folded: str, idx: int) -> bool:
    pos = idx - 1
    while pos >= 0 and folded[pos] == " ":
        pos -= 1
    for w in _FOREIGN_PREFIXES:
        start = pos - len(w) + 1
        if (
            start >= 0
            and folded[start:pos + 1] == w
            and (start == 0 or not folded[start - 1].isalpha())
        ):
            return True
    return False


def _scan_weak_number(text: str, folded: str, start: int) -> Span | None:
    pos = start
    words_skipped = 0
    limit = start + 30
    while pos < len(text):
        if pos >= limit:
            return None
        ch = text[pos]
        if ch in " \t:,":
            pos += 1
            continue
        if ch == ".":
            return None
        if words_skipped < 2:
            matched = False
            for w in _SERIES_WORDS:
                wf = w.casefold().replace("ё", "е")
                if folded.startswith(wf, pos) and (
                    pos == 0 or not folded[pos - 1].isalpha()
                ) and (pos + len(wf) >= len(folded) or not folded[pos + len(wf)].isalpha()):
                    pos += len(w)
                    words_skipped += 1
                    matched = True
                    break
            if matched:
                continue
        break
    if pos >= limit:
        return None
    digits = []
    positions = []
    i = pos
    while i < len(text) and len(digits) < 12:
        if text[i].isdigit():
            digits.append(text[i])
            positions.append(i)
            i += 1
        elif text[i] == " " and digits:
            j = i
            while j < len(text) and text[j] == " ":
                j += 1
            if j < len(text) and text[j].isdigit() and (j - i) == 1:
                digits.append(text[j])
                positions.append(j)
                i = j + 1
            else:
                break
        else:
            break
    if len(digits) < 6:
        return None
    if i < len(text):
        if text[i].isdigit():
            return None
        if text[i] == " ":
            j = i
            while j < len(text) and text[j] == " ":
                j += 1
            if j < len(text) and text[j].isdigit() and (j - i) == 1:
                return None
    if _is_phone(digits):
        return None
    return Span(positions[0], positions[-1] + 1, "passport", PRIORITY["passport"])


def _find_weak(text: str, folded: str) -> list[Span]:
    spans = []
    for key in _PASSPORT_KEYS:
        kf = key.casefold().replace("ё", "е")
        idx = 0
        while True:
            idx = folded.find(kf, idx)
            if idx == -1:
                break
            left_ok = idx == 0 or not folded[idx - 1].isalpha()
            right_ok = idx + len(kf) >= len(folded) or not folded[idx + len(kf)].isalpha()
            if left_ok and right_ok and not _has_foreign_prefix(folded, idx):
                span = _scan_weak_number(text, folded, idx + len(kf))
                if span is not None:
                    spans.append(span)
            idx += len(kf)
    return spans


def find(text: str) -> list[Span]:
    folded = text.casefold().replace("ё", "е")
    spans = []
    for m in _PASSPORT_RE.finditer(text):
        start, end = m.start(), m.end()
        has_passport = has_keyword(folded, start, end, _PASSPORT_KEYS, 40)
        has_series = all(has_keyword(folded, start, end, (w,), 40) for w in _LETTER_SERIES)
        if has_passport or has_series:
            spans.append(Span(start, end, "passport", PRIORITY["passport"]))
    spans.extend(_find_weak(text, folded))
    return spans