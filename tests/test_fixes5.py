import pytest

from app import pipeline
from app.profiles import load_profiles

PROFILES = load_profiles()
CHECKER = PROFILES["checker"]


def mask(text: str) -> str:
    return pipeline.apply(text, pipeline.detect(text, CHECKER))


FILLER_CASE_CASES = [
    ("паспорт Серия 12 3456789", "паспорт Серия ** *******"),
    ("Паспорт СЕРИЯ 123 445343", "Паспорт СЕРИЯ *** ******"),
    ("паспорт серия 12 3456789", "паспорт серия ** *******"),
    ("паспорт 123 445343", "паспорт *** ******"),
]


@pytest.mark.parametrize("text,expected", FILLER_CASE_CASES)
def test_filler_case_insensitive(text: str, expected: str):
    assert mask(text) == expected


LONG_GROUP_CASES = [
    ("паспорт 1234567890123", "паспорт 1234567890123"),
    ("паспорт 123456789012", "паспорт 12******90**"),
    ("паспорт 123445343", "паспорт *********"),
]


@pytest.mark.parametrize("text,expected", LONG_GROUP_CASES)
def test_long_group_not_truncated(text: str, expected: str):
    assert mask(text) == expected


WINDOW_CASES = [
    ("паспорт" + " " * 40 + "123456", "паспорт" + " " * 40 + "123456"),
    ("паспорт 123456", "паспорт ******"),
    ("паспорт просрочен. Заявка 123456", "паспорт просрочен. Заявка 123456"),
    ("паспорт серия 12 3456789", "паспорт серия ** *******"),
]


@pytest.mark.parametrize("text,expected", WINDOW_CASES)
def test_first_digit_window(text: str, expected: str):
    assert mask(text) == expected


UNCHANGED_CASES = [
    ("серия 4509 номер 123456", "серия 45** номер ****56"),
    ("паспорт 4509 123456", "паспорт 45** ****56"),
    ("паспорт 45 09 123456", "паспорт 45 ** ****56"),
    ("4509 123456", "4509 123456"),
    ("заграничный паспорт 121234567", "заграничный паспорт 12*******"),
    ("загранпаспорт 12 1234567", "загранпаспорт 12 *******"),
    ("Клиентка Юлия Сергеевна Кузнецова, паспорт 123 445343, любит играть в сквош!",
     "Клиентка Ю. С. К., паспорт *** ******, любит играть в сквош!"),
]


@pytest.mark.parametrize("text,expected", UNCHANGED_CASES)
def test_behavior_unchanged(text: str, expected: str):
    assert mask(text) == expected