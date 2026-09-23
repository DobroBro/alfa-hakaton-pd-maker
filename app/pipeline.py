import json
import logging

from app import detectors
from app.maskers import mask_fragment
from app.types import PRIORITY, STRUCTURAL_TYPES, Span

logger = logging.getLogger("pd")

DETECTORS = [
    ("email", detectors.email.find),
    ("card_number", detectors.card.find),
    ("inn", detectors.inn.find),
    ("passport", detectors.passport.find),
    ("foreign_passport", detectors.foreign_passport.find),
    ("driver_license", detectors.driver_license.find),
    ("department_code", detectors.department_code.find),
    ("phone", detectors.phone.find),
    ("secrets", detectors.secrets.find),
    ("dates", detectors.dates.find),
    ("address", detectors.address.find),
    ("cardholder", detectors.cardholder.find),
    ("fio", detectors.fio.find),
    ("document_context", detectors.document_context.find),
]


def _gap(a: Span, b: Span) -> int:
    if a.end <= b.start:
        return b.start - a.end
    if b.end <= a.start:
        return a.start - b.end
    return 0


def _replace(span: Span, type_: str) -> Span:
    return Span(span.start, span.end, type_, PRIORITY[type_], span.mask)


def resolve_overlaps(spans: list[Span]) -> list[Span]:
    accepted: list[Span] = []
    ordered = sorted(spans, key=lambda s: (-s.priority, -(s.end - s.start), s.start))
    for span in ordered:
        remaining = [span]
        for acc in accepted:
            new_remaining = []
            for cur in remaining:
                if cur.end <= acc.start or cur.start >= acc.end:
                    new_remaining.append(cur)
                    continue
                if cur.type in STRUCTURAL_TYPES:
                    continue
                left = Span(cur.start, acc.start, cur.type, cur.priority, cur.mask)
                right = Span(acc.end, cur.end, cur.type, cur.priority, cur.mask)
                if left.end - left.start >= 2:
                    new_remaining.append(left)
                if right.end - right.start >= 2:
                    new_remaining.append(right)
            remaining = new_remaining
            if not remaining:
                break
        accepted.extend(remaining)
    return accepted


def drop_address_inside_birth_place(spans: list[Span]) -> list[Span]:
    birth_places = [s for s in spans if s.type == "birth_place"]
    if not birth_places:
        return spans
    result = []
    for s in spans:
        if s.type == "address" and any(
            bp.start <= s.start and s.end <= bp.end for bp in birth_places
        ):
            continue
        result.append(s)
    return result


def apply_combo(spans: list[Span]) -> list[Span]:
    has_card = any(s.type == "card_number" and s.mask for s in spans)
    if has_card:
        return spans
    result = []
    for s in spans:
        if s.type in ("pin", "cvv"):
            result.append(Span(s.start, s.end, s.type, s.priority, False))
        else:
            result.append(s)
    return result


def detect(text: str, profile) -> list[Span]:
    spans: list[Span] = []
    for name, finder in DETECTORS:
        try:
            spans += finder(text)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                json.dumps(
                    {
                        "event": "detector_error",
                        "detector": name,
                        "error_type": type(exc).__name__,
                    },
                    ensure_ascii=False,
                )
            )
    allowed = set(profile.types)
    spans = [s for s in spans if s.type in allowed or s.type == "date_candidate"]
    head = [s for s in spans if s.type != "date_candidate"]
    candidates = [s for s in spans if s.type == "date_candidate"]
    head = drop_address_inside_birth_place(head)
    head = resolve_overlaps(head)
    promoted = []
    anchors = [s for s in head if s.type in ("fio", "passport")]
    for cand in candidates:
        if any(_gap(cand, a) <= 80 for a in anchors):
            promoted.append(_replace(cand, "birth_date"))
    head = resolve_overlaps(head + promoted)
    head = drop_address_inside_birth_place(head)
    if profile.combo_rules:
        head = apply_combo(head)
    return head


def apply(text: str, spans: list[Span], style: str = "reference") -> str:
    if style == "token":
        return _apply_token(text, spans)
    pieces = []
    cursor = 0
    for span in sorted((s for s in spans if s.mask), key=lambda s: s.start):
        if span.end <= cursor:
            continue
        if span.start < cursor:
            pieces.append(mask_fragment(span.type, text[cursor:span.end]))
            cursor = span.end
            continue
        if span.end > len(text):
            continue
        pieces.append(text[cursor:span.start])
        pieces.append(mask_fragment(span.type, text[span.start:span.end]))
        cursor = span.end
    pieces.append(text[cursor:])
    return "".join(pieces)


def _apply_token(text: str, spans: list[Span]) -> str:
    counters: dict[str, int] = {}
    pieces = []
    cursor = 0
    for span in sorted((s for s in spans if s.mask), key=lambda s: s.start):
        if span.end <= cursor:
            continue
        if span.start < cursor:
            counters[span.type] = counters.get(span.type, 0) + 1
            pieces.append(f"[{span.type.upper()}_{counters[span.type]}]")
            cursor = span.end
            continue
        if span.end > len(text):
            continue
        pieces.append(text[cursor:span.start])
        counters[span.type] = counters.get(span.type, 0) + 1
        pieces.append(f"[{span.type.upper()}_{counters[span.type]}]")
        cursor = span.end
    pieces.append(text[cursor:])
    return "".join(pieces)