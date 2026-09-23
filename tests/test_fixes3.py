import pytest

from app import pipeline
from app.profiles import load_profiles

PROFILES = load_profiles()
CHECKER = PROFILES["checker"]
VAULT = PROFILES["vault"]


def mask(text: str) -> str:
    return pipeline.apply(text, pipeline.detect(text, CHECKER))


def mask_vault(text: str) -> str:
    return pipeline.apply(text, pipeline.detect(text, VAULT), VAULT.mask_style)


CARD_FIO_CASES = [
    ("держатель карты IVAN IVANOV", "держатель карты I. I."),
    ("держатель IVAN IVANOV", "держатель I. I."),
]


@pytest.mark.parametrize("text,expected", CARD_FIO_CASES)
def test_card_word_not_in_fio(text: str, expected: str):
    assert mask(text) == expected


FOREIGN_PASSPORT_CASES = [
    ("загранпаспорт 12 1234567", "загранпаспорт 12 *******"),
    ("заграничный паспорт 121234567", "заграничный паспорт 12*******"),
    ("12 1234567", "12 1234567"),
]


@pytest.mark.parametrize("text,expected", FOREIGN_PASSPORT_CASES)
def test_foreign_passport(text: str, expected: str):
    assert mask(text) == expected


RULES_CASES = [
    ("поэт Александр Сергеевич Пушкин", "поэт Александр Сергеевич Пушкин"),
    ("отделение банка, ул. Каланчевская, д. 27", "отделение банка, ул. Каланчевская, д. 27"),
    ("клиент живёт здесь", "клиент живёт здесь"),
    ("клиент иван петров", "клиент И. П."),
]


@pytest.mark.parametrize("text,expected", RULES_CASES)
def test_rules_config(text: str, expected: str):
    assert mask(text) == expected


TOKEN_CASES = [
    ("Клиент Иванов Иван Иванович, паспорт 4509 123456",
     "Клиент [FIO_1], паспорт [PASSPORT_1]"),
    ("ivan.petrov@mail.ru и petr@mail.ru", "[EMAIL_1] и [EMAIL_2]"),
]


@pytest.mark.parametrize("text,expected", TOKEN_CASES)
def test_token_style(text: str, expected: str):
    assert mask_vault(text) == expected


def test_token_style_reference_unchanged():
    text = "Клиент Иванов Иван Иванович, паспорт 4509 123456"
    assert mask(text) == "Клиент И. И. И., паспорт 45** ****56"