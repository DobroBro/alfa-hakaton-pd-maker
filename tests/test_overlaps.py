from app.pipeline import resolve_overlaps
from app.types import Span


def test_passport_beats_phone():
    spans = [
        Span(0, 11, "passport", 70),
        Span(0, 11, "phone", 50),
    ]
    result = resolve_overlaps(spans)
    assert [s.type for s in result] == ["passport"]


def test_birth_date_cuts_issuer():
    spans = [
        Span(0, 30, "passport_issuer", 10),
        Span(20, 30, "birth_date", 30),
    ]
    result = resolve_overlaps(spans)
    types = sorted((s.type, s.start, s.end) for s in result)
    assert ("birth_date", 20, 30) in types
    assert ("passport_issuer", 0, 20) in types