from __future__ import annotations

import re


def conservative_cleanup(text: str) -> str:
    """Whitespace/punctuation cleanup only; never silently changes lexical letters."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *([،؛؟.!]) *", r"\1 ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()

