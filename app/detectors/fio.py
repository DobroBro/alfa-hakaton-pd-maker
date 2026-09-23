import re

from app.context import has_keyword_left, has_stop_context
from app.settings import GAZETTEER, RULES
from app.types import PRIORITY, Span

_WORD_RE = re.compile(
    r"(?<![A-Za-zА-Яа-яЁё])[A-Za-zА-Яа-яЁё]{2,}(?:-[A-Za-zА-Яа-яЁё]{2,})?(?![A-Za-zА-Яа-яЁё])"
)

_PERSONAL_KEYS = tuple(RULES.get("personal_keys", []))
_POET_STOP = tuple(RULES.get("poet_stop", []))
_SURNAMES = tuple(GAZETTEER.get("surnames", []))

_PATR_SUFFIXES = ("ович", "евич", "овна", "евна", "ична")

_NON_NAME_WORDS = tuple(RULES.get("fio_non_name", []))
_CARD_WORDS = tuple(RULES.get("fio_card_words", []))

_INITIALS_RE = re.compile(
    r"(?<![A-Za-zА-Яа-яЁё])[A-Za-zА-Яа-яЁё]{2,}(?:-[A-Za-zА-Яа-яЁё]{2,})?\s+"
    r"[A-ZА-ЯЁ]\.\s+[A-ZА-ЯЁ]\."
    r"|[A-ZА-ЯЁ]\.\s+[A-ZА-ЯЁ]\.\s+"
    r"[A-Za-zА-Яа-яЁё]{2,}(?:-[A-Za-zА-Яа-яЁё]{2,})?"
)


def _is_patronymic(word: str) -> bool:
    w = word.casefold().replace("ё", "е")
    return any(w.endswith(s) for s in _PATR_SUFFIXES)


def _spaces_only(text: str, end1: int, start2: int) -> bool:
    between = text[end1:start2]
    return bool(between) and all(ch == " " for ch in between)


def _is_fio_window(folded: str, text: str, span_start: int, words: list[str]) -> bool:
    has_patr = any(_is_patronymic(w) for w in words)
    has_key = has_keyword_left(folded, span_start, _PERSONAL_KEYS, 40)
    if not has_patr and not has_key:
        return False
    if any(w.casefold().replace("ё", "е") in _PERSONAL_KEYS for w in words):
        return False
    if any(w.casefold().replace("ё", "е") in _POET_STOP for w in words):
        return False
    if any(w.casefold().replace("ё", "е") in _CARD_WORDS for w in words):
        return False
    if not has_patr and any(w.casefold().replace("ё", "е") in _NON_NAME_WORDS for w in words):
        return False
    if not has_key:
        for w in words:
            if w.casefold().replace("ё", "е") in _SURNAMES:
                return False
    return not has_stop_context(folded, span_start, span_start, _POET_STOP)


def _single_word_after_key(text: str, folded: str) -> list[Span]:
    spans = []
    for kw in ("фамилия", "имя", "отчество"):
        idx = folded.find(kw)
        while idx != -1:
            left_ok = idx == 0 or not folded[idx - 1].isalpha()
            right_ok = idx + len(kw) >= len(folded) or not folded[idx + len(kw)].isalpha()
            if left_ok and right_ok:
                m = _WORD_RE.search(text, idx + len(kw))
                if m:
                    between = text[idx + len(kw):m.start()]
                    if all(ch in " :\t" for ch in between):
                        spans.append(Span(m.start(), m.end(), "fio", PRIORITY["fio"]))
            idx = folded.find(kw, idx + 1)
    return spans


def _initials_ok(folded: str, text: str, start: int, end: int) -> bool:
    if has_stop_context(folded, start, start, _POET_STOP):
        return False
    span_words = text[start:end].split()
    if any(w.casefold().replace("ё", "е") in _POET_STOP for w in span_words):
        return False
    has_key = has_keyword_left(folded, start, _PERSONAL_KEYS, 40)
    if has_key:
        return True
    name_word = span_words[-1]
    return name_word.casefold().replace("ё", "е") not in _SURNAMES


def find(text: str) -> list[Span]:
    folded = text.casefold().replace("ё", "е")
    words = [(m.start(), m.end(), m.group()) for m in _WORD_RE.finditer(text)]
    spans = []
    i = 0
    while i < len(words):
        s0, e0, w0 = words[i]
        if w0.casefold().replace("ё", "е") in _PERSONAL_KEYS:
            i += 1
            continue
        if i + 2 < len(words):
            s1, e1, w1 = words[i + 1]
            s2, e2, w2 = words[i + 2]
            if (
                _spaces_only(text, e0, s1)
                and _spaces_only(text, e1, s2)
                and _is_fio_window(folded, text, s0, [w0, w1, w2])
            ):
                spans.append(Span(s0, e2, "fio", PRIORITY["fio"]))
                i += 3
                continue
        if i + 1 < len(words):
            s1, e1, w1 = words[i + 1]
            if _spaces_only(text, e0, s1) and _is_fio_window(folded, text, s0, [w0, w1]):
                spans.append(Span(s0, e1, "fio", PRIORITY["fio"]))
                i += 2
                continue
        i += 1
    for m in _INITIALS_RE.finditer(text):
        if _initials_ok(folded, text, m.start(), m.end()):
            spans.append(Span(m.start(), m.end(), "fio", PRIORITY["fio"]))
    spans.extend(_single_word_after_key(text, folded))
    return spans