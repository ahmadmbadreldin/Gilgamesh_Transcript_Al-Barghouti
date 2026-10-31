from __future__ import annotations

import re

DIACRITICS = re.compile(r"[\u064B-\u065F\u0670]")


def letters_only(text: str) -> str:
    return DIACRITICS.sub("", text)


def assert_same_letters(before: str, after: str) -> None:
    arabic = lambda s: "".join(re.findall(r"[\u0621-\u064A]", letters_only(s)))
    if arabic(before) != arabic(after):
        raise ValueError("Diacritization changed base letters")


def automatic_diacritize(text: str) -> str:
    from mishkal.tashkeel import TashkeelClass

    engine = TashkeelClass()
    result = engine.tashkeel(text).strip()
    assert_same_letters(text, result)
    return result

