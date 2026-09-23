import re

from app.context import has_keyword
from app.types import PRIORITY, Span

_BIRTH_KEYS = ("дата рождения", "родился", "родилась", "д.р.")
_ISSUE_KEYS = ("дата выдачи", "выдан", "выдана")

_NUM_RE = re.compile(
    r"(?<!\d)(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}[./-]\d{1,2}[./-]\d{1,2})(?!\d)"
)

_DAY_WORDS = [
    "первое", "второе", "третье", "четвертое", "пятое", "шестое", "седьмое",
    "восьмое", "девятое", "десятое", "одиннадцатое", "двенадцатое", "тринадцатое",
    "четырнадцатое", "пятнадцатое", "шестнадцатое", "семнадцатое", "восемнадцатое",
    "девятнадцатое", "двадцатое", "двадцать первое", "двадцать второе",
    "двадцать третье", "двадцать четвертое", "двадцать пятое", "двадцать шестое",
    "двадцать седьмое", "двадцать восьмое", "двадцать девятое", "тридцатое",
    "тридцать первое",
    "первого", "второго", "третьего", "четвертого", "пятого", "шестого",
    "седьмого", "восьмого", "девятого", "десятого", "одиннадцатого",
    "двенадцатого", "тринадцатого", "четырнадцатого", "пятнадцатого",
    "шестнадцатого", "семнадцатого", "восемнадцатого", "девятнадцатого",
    "двадцатого", "двадцать первого", "двадцать второго", "двадцать третьего",
    "двадцать четвертого", "двадцать пятого", "двадцать шестого",
    "двадцать седьмого", "двадцать восьмого", "двадцать девятого",
    "тридцатого", "тридцать первого",
]

_MONTH_WORDS = [
    "января", "февраля", "марта", "апреля", "мая", "июня", "июля",
    "августа", "сентября", "октября", "ноября", "декабря",
    "январь", "февраль", "март", "апрель", "май", "июнь", "июль",
    "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
]

_day_alt = "|".join(sorted(_DAY_WORDS, key=len, reverse=True))
_month_alt = "|".join(sorted(_MONTH_WORDS, key=len, reverse=True))

_TEXT_RE = re.compile(
    r"(?<!\d)(?:\d{1,2}|" + _day_alt + r")\s+(?:" + _month_alt + r")\s+\d{4}(?!\d)"
)


def _valid(parts: list[str]) -> bool:
    a, b, c = int(parts[0]), int(parts[1]), int(parts[2])
    if len(str(a)) == 4:
        return 1 <= b <= 12 and 1 <= c <= 31
    if 1 <= b <= 12 and 1 <= a <= 31:
        return True
    return 1 <= a <= 12 and 1 <= b <= 31


def _date_type(folded: str, start: int, end: int) -> str:
    if has_keyword(folded, start, end, _BIRTH_KEYS, 40):
        return "birth_date"
    if has_keyword(folded, start, end, _ISSUE_KEYS, 40):
        return "passport_issue_date"
    return "date_candidate"


def find(text: str) -> list[Span]:
    folded = text.casefold().replace("ё", "е")
    spans = []
    for m in _NUM_RE.finditer(text):
        parts = re.split(r"[./-]", m.group())
        if len(parts) == 3 and _valid(parts):
            t = _date_type(folded, m.start(), m.end())
            spans.append(Span(m.start(), m.end(), t, PRIORITY[t]))
    for m in _TEXT_RE.finditer(folded):
        t = _date_type(folded, m.start(), m.end())
        spans.append(Span(m.start(), m.end(), t, PRIORITY[t]))
    return spans