from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    type: str
    priority: int
    mask: bool = True


PRIORITY = {
    "email": 100,
    "card_number": 90,
    "inn": 80,
    "passport": 70,
    "foreign_passport": 65,
    "driver_license": 60,
    "department_code": 55,
    "phone": 50,
    "cvv": 40,
    "pin": 35,
    "birth_date": 30,
    "passport_issue_date": 30,
    "date_candidate": 30,
    "address": 20,
    "cardholder": 15,
    "fio": 14,
    "birth_place": 10,
    "citizenship": 10,
    "passport_issuer": 10,
}

STRUCTURAL_TYPES = {
    "email",
    "card_number",
    "inn",
    "passport",
    "foreign_passport",
    "driver_license",
    "department_code",
    "phone",
    "cvv",
    "pin",
    "birth_date",
    "passport_issue_date",
}

FREE_TEXT_TYPES = {
    "address",
    "cardholder",
    "fio",
    "birth_place",
    "citizenship",
    "passport_issuer",
}