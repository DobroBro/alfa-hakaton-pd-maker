import re

from app.types import PRIORITY, Span

_WORD_RE = re.compile(
    r"(?<![A-Za-zА-Яа-яЁё])[A-Za-zА-Яа-яЁё]{2,}(?:-[A-Za-zА-Яа-яЁё]{2,})?(?![A-Za-zА-Яа-яЁё])"
)

_KEYS = ("держатель", "cardholder")
_FILLER = ("карты", "карта")


def find(text: str) -> list[Span]:
    folded = text.casefold().replace("ё", "е")
    spans = []
    for kw in _KEYS:
        idx = folded.find(kw)
        while idx != -1:
            left_ok = idx == 0 or not folded[idx - 1].isalpha()
            right_ok = idx + len(kw) >= len(folded) or not folded[idx + len(kw)].isalpha()
            if left_ok and right_ok:
                words = []
                pos = idx + len(kw)
                while len(words) < 3:
                    m = _WORD_RE.search(text, pos)
                    if not m:
                        break
                    between = text[pos:m.start()]
                    if not all(ch in " \t" for ch in between):
                        break
                    w = m.group().casefold().replace("ё", "е")
                    if w in _FILLER and not words:
                        pos = m.end()
                        continue
                    words.append((m.start(), m.end()))
                    pos = m.end()
                if len(words) >= 2:
                    spans.append(
                        Span(words[0][0], words[-1][1], "cardholder", PRIORITY["cardholder"])
                    )
            idx = folded.find(kw, idx + 1)
    return spans