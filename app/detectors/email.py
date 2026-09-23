import re

from app.types import PRIORITY, Span

_EMAIL_RE = re.compile(
    r"(?<![A-Za-z0-9._%+\-])[A-Za-z0-9._%+\-]{1,64}@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}(?![A-Za-z0-9])"
)


def find(text: str) -> list[Span]:
    spans = []
    for m in _EMAIL_RE.finditer(text):
        spans.append(Span(m.start(), m.end(), "email", PRIORITY["email"]))
    return spans