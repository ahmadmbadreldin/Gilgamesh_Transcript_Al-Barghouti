from __future__ import annotations


def preserve_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.splitlines()]

