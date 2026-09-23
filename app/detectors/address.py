import re

from app.context import has_stop_context
from app.settings import RULES
from app.types import PRIORITY, Span

_CITY = ("г.", "город", "пос.")
_STREET = ("ул.", "улица", "пр-т", "проспект", "пер.", "переулок", "шоссе", "наб.", "б-р", "бульвар")
_HOUSE = ("д.", "дом", "корп.", "корпус", "строение", "стр.", "кв.", "квартира")

_DOT_MARKER = r"(?:г\.|ул\.|д\.|кв\.|корп\.|стр\.|пос\.|пер\.|наб\.|б-р|пр-т)"
_WORD_MARKER = r"(?:город|дом|улица|квартира|проспект|переулок|шоссе|бульвар|корпус|строение)"
_TOKEN = r"[A-Za-zА-Яа-яЁё0-9]+(?:-[A-Za-zА-Яа-яЁё0-9]+)?(?:/\d+)?"

_COMPONENT_RE = re.compile(
    r"(?<![A-Za-zА-Яа-яЁё.])"
    r"(?P<marker>" + _DOT_MARKER + r"\s*|" + _WORD_MARKER + r"\s+)"
    r"(?P<value>" + _TOKEN + r")"
)
_INDEX_RE = re.compile(r"(?<!\d)\d{6}(?!\d)")
_COUNTRY_RE = re.compile(
    r"(?<![A-Za-zА-Яа-яЁё])(?:россия|рф)(?![A-Za-zА-Яа-яЁё])", re.IGNORECASE
)

_STOP = tuple(RULES.get("address_stop", []))

_HOUSE_VALUE_RE = re.compile(r"\d+[A-Za-zА-Яа-яЁё]?(?:/\d+)?")


def _marker_type(marker: str) -> str:
    if marker in _CITY:
        return "city"
    if marker in _STREET:
        return "street"
    return "house"


def _valid_value(marker: str, value: str) -> bool:
    if marker in _HOUSE:
        return bool(_HOUSE_VALUE_RE.fullmatch(value))
    return any(ch.isalpha() for ch in value)


def _gap_is_separator(text: str, end1: int, start2: int) -> bool:
    gap = text[end1:start2]
    return all(ch in " \t," for ch in gap)


def find(text: str) -> list[Span]:
    folded = text.casefold().replace("ё", "е")
    comps = []
    for m in _COMPONENT_RE.finditer(text):
        marker = m.group("marker").strip()
        value = m.group("value")
        if not _valid_value(marker, value):
            continue
        comps.append((m.start(), m.end(), _marker_type(marker)))
    for m in _INDEX_RE.finditer(text):
        comps.append((m.start(), m.end(), "index"))
    for m in _COUNTRY_RE.finditer(text):
        comps.append((m.start(), m.end(), "country"))
    if not comps:
        return []
    comps.sort(key=lambda c: c[0])

    clusters = []
    cur = [comps[0]]
    for c in comps[1:]:
        if _gap_is_separator(text, cur[-1][1], c[0]):
            cur.append(c)
        else:
            clusters.append(cur)
            cur = [c]
    clusters.append(cur)

    result = []
    for cluster in clusters:
        types = {c[2] for c in cluster}
        if not (types & {"city", "street", "house"}):
            continue
        start = cluster[0][0]
        end = cluster[-1][1]
        if has_stop_context(folded, start, end, _STOP):
            continue
        result.append(Span(start, end, "address", PRIORITY["address"]))
    return result