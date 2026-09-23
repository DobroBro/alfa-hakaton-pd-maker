def star_digits(fragment: str, keep: set[int]) -> str:
    chars = list(fragment)
    for i, ch in enumerate(chars):
        if ch.isdigit() and i not in keep:
            chars[i] = "*"
    return "".join(chars)


def digit_indexes(fragment: str) -> list[int]:
    return [i for i, ch in enumerate(fragment) if ch.isdigit()]


def mask_phone(fragment: str) -> str:
    d = digit_indexes(fragment)
    keep = set()
    if len(d) >= 11:
        keep.add(d[0])
    if len(d) >= 2:
        keep.add(d[-2])
        keep.add(d[-1])
    return star_digits(fragment, keep)


def mask_card_number(fragment: str) -> str:
    d = digit_indexes(fragment)
    keep = set()
    if len(d) >= 8:
        keep.update(d[:4])
        keep.update(d[-4:])
    return star_digits(fragment, keep)


def mask_inn(fragment: str) -> str:
    d = digit_indexes(fragment)
    keep = set()
    if len(d) >= 4:
        keep.update(d[:2])
        keep.update(d[-2:])
    return star_digits(fragment, keep)


def mask_passport(fragment: str) -> str:
    d = digit_indexes(fragment)
    keep = set()
    if len(d) >= 10:
        keep.update([d[0], d[1], d[8], d[9]])
    return star_digits(fragment, keep)


def mask_department_code(fragment: str) -> str:
    return star_digits(fragment, set())


def mask_cvv(fragment: str) -> str:
    return star_digits(fragment, set())


def mask_pin(fragment: str) -> str:
    return star_digits(fragment, set())


def mask_birth_date(fragment: str) -> str:
    if any(ch.isalpha() for ch in fragment):
        return "**.**.****"
    if any(ch.isdigit() for ch in fragment):
        return star_digits(fragment, set())
    return "**.**.****"


def mask_email(fragment: str) -> str:
    at = fragment.find("@")
    if at == -1:
        return fragment
    local = fragment[:at]
    domain = fragment[at:]
    if not local:
        return fragment
    return local[0] + "***" + domain


def _mask_name_word(word: str) -> str:
    parts = word.split("-")
    masked = []
    for part in parts:
        if not part:
            masked.append(part)
            continue
        masked.append(part[0].upper() + ".")
    return "-".join(masked)


def mask_fio(fragment: str) -> str:
    words = fragment.split()
    return " ".join(_mask_name_word(w) for w in words)


def mask_cardholder(fragment: str) -> str:
    return mask_fio(fragment)


_ADDRESS_MARKERS = {
    "г.": "г.",
    "город": "город",
    "пос.": "пос.",
    "ул.": "ул.",
    "улица": "улица",
    "пр-т": "пр-т",
    "проспект": "проспект",
    "пер.": "пер.",
    "переулок": "переулок",
    "шоссе": "шоссе",
    "наб.": "наб.",
    "б-р": "б-р",
    "бульвар": "бульвар",
    "д.": "д.",
    "дом": "дом",
    "корп.": "корп.",
    "корпус": "корпус",
    "строение": "строение",
    "стр.": "стр.",
    "кв.": "кв.",
    "квартира": "квартира",
}


def mask_address(fragment: str) -> str:
    result = []
    i = 0
    n = len(fragment)
    while i < n:
        matched = False
        for marker in sorted(_ADDRESS_MARKERS, key=len, reverse=True):
            if fragment.startswith(marker, i):
                result.append(marker)
                i += len(marker)
                while i < n and fragment[i] in " \t":
                    result.append(fragment[i])
                    i += 1
                start = i
                while i < n and fragment[i] not in " \t,;":
                    i += 1
                result.append("*" * (i - start))
                matched = True
                break
        if matched:
            continue
        if (
            i + 6 <= n
            and fragment[i:i + 6].isdigit()
            and (i == 0 or not fragment[i - 1].isdigit())
            and (i + 6 == n or not fragment[i + 6].isdigit())
        ):
            result.append("*" * 6)
            i += 6
            continue
        country_matched = False
        for cw in ("россия", "рф"):
            if fragment[i:i + len(cw)].casefold() == cw and (
                i == 0 or not fragment[i - 1].isalpha()
            ) and (i + len(cw) == n or not fragment[i + len(cw)].isalpha()):
                result.append("*" * len(cw))
                i += len(cw)
                country_matched = True
                break
        if country_matched:
            continue
        result.append(fragment[i])
        i += 1
    return "".join(result)


def mask_citizenship(fragment: str) -> str:
    return _mask_marker_value(fragment)


def mask_passport_issuer(fragment: str) -> str:
    return _mask_marker_value(fragment)


def mask_birth_place(fragment: str) -> str:
    return _mask_marker_value(fragment)


_MARKER_STRINGS = ("кем выдан", "место рождения", "гражданство", "орган")


def _mask_marker_value(fragment: str) -> str:
    for marker in sorted(_MARKER_STRINGS, key=len, reverse=True):
        if fragment.startswith(marker):
            rest = fragment[len(marker):]
            i = 0
            while i < len(rest) and rest[i] in " \t:":
                i += 1
            return fragment[: len(marker) + i] + "*" * (len(rest) - i)
    return fragment


def mask_foreign_passport(fragment: str) -> str:
    d = digit_indexes(fragment)
    keep = set()
    if len(d) >= 2:
        keep.update(d[:2])
    return star_digits(fragment, keep)


MASKERS = {
    "phone": mask_phone,
    "card_number": mask_card_number,
    "inn": mask_inn,
    "passport": mask_passport,
    "driver_license": mask_passport,
    "department_code": mask_department_code,
    "cvv": mask_cvv,
    "pin": mask_pin,
    "birth_date": mask_birth_date,
    "passport_issue_date": mask_birth_date,
    "email": mask_email,
    "fio": mask_fio,
    "cardholder": mask_cardholder,
    "address": mask_address,
    "citizenship": mask_citizenship,
    "passport_issuer": mask_passport_issuer,
    "birth_place": mask_birth_place,
    "foreign_passport": mask_foreign_passport,
}


def mask_fragment(pii_type: str, fragment: str) -> str:
    """fragment == text[start:end]. Does not look outside. Deterministic."""
    masker = MASKERS.get(pii_type)
    if masker is None:
        return fragment
    return masker(fragment)