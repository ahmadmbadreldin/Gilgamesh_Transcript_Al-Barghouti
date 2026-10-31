from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from diacritization import automatic_diacritize


NAME_RULES = [
    (re.compile(r"\bجلجام\s+ش\b"), "جلجامش"),
    (re.compile(r"\bانكيدو\b"), "أنكيدو"),
    (re.compile(r"\bخمبابا\b"), "خُمبابا"),
    (re.compile(r"\bاوتنابشتم\b"), "أوتنابشتم"),
    (re.compile(r"\bاوتا?\s*نبشتم\b"), "أوتنابشتم"),
    (re.compile(r"\bاوروك\b"), "أُورُوك"),
    (re.compile(r"\bاور\s*شنابي\b"), "أورشنابي"),
]


def clean_line(line: str) -> tuple[str, dict[str, int]]:
    line = line.strip().replace("\ufffd", "")
    changes: dict[str, int] = {}
    for pattern, replacement in NAME_RULES:
        line, count = pattern.subn(replacement, line)
        if count:
            changes[replacement] = changes.get(replacement, 0) + count
    line = re.sub(r"\s+", " ", line).strip()
    return line, changes


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("human", type=Path)
    p.add_argument("youtube", type=Path)
    p.add_argument("reviewed_dir", type=Path)
    p.add_argument("final_txt", type=Path)
    p.add_argument("--youtube-start-line", type=int, default=594, help="1-based line where continuation begins")
    args = p.parse_args()

    human_lines = []
    for raw in args.human.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or "الملحمة ليست مكتوبة" in line:
            continue
        human_lines.append(line)

    youtube_all = args.youtube.read_text(encoding="utf-8-sig").splitlines()
    continuation_raw = youtube_all[args.youtube_start_line - 1:]
    continuation = []
    corrections: dict[str, int] = {}
    excluded_events = []
    for raw in continuation_raw:
        line, changes = clean_line(raw)
        for key, count in changes.items():
            corrections[key] = corrections.get(key, 0) + count
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            excluded_events.append(line)
            continue
        continuation.append(line)

    auto_diacritized = []
    for i, line in enumerate(continuation, start=1):
        try:
            auto_diacritized.append(automatic_diacritize(line))
        except Exception as exc:
            auto_diacritized.append(line)
            corrections[f"فشل تشكيل آلي في سطر {i}: {type(exc).__name__}"] = 1

    separator = "[يَنْتَهِي هُنا نِطاقُ النَّسْخَةِ البَشَرِيَّةِ المُشَكَّلةِ، وَيَبْدَأُ النَّصُّ المُقابَلُ آليًّا والمُشَكَّلُ مَسْوَدَّةً لِلمُراجَعَةِ]"
    final_lines = [
        "مَلْحَمَةُ جِلْجَامِشَ",
        "تَمِيمُ البَرْغُوثِيُّ",
        "",
        *human_lines,
        "",
        separator,
        "",
        *auto_diacritized,
    ]
    args.reviewed_dir.mkdir(parents=True, exist_ok=True)
    args.final_txt.parent.mkdir(parents=True, exist_ok=True)
    base_path = args.reviewed_dir / "النص_المرجعي_قبل_التشكيل_الآلي.txt"
    auto_path = args.reviewed_dir / "النص_المشكل_آليا_للمراجعة.txt"
    meta_path = args.reviewed_dir / "build_metadata.json"
    base_path.write_text("\n".join(human_lines + [""] + continuation) + "\n", encoding="utf-8")
    auto_path.write_text("\n".join(auto_diacritized) + "\n", encoding="utf-8")
    args.final_txt.write_text("\n".join(final_lines) + "\n", encoding="utf-8")
    meta = {
        "human_lines": len(human_lines),
        "youtube_start_line_1_based": args.youtube_start_line,
        "continuation_lines": len(continuation),
        "automatic_diacritized_lines": len(auto_diacritized),
        "excluded_sound_event_lines": excluded_events,
        "deterministic_name_corrections": corrections,
        "human_words": len(" ".join(human_lines).split()),
        "continuation_words": len(" ".join(continuation).split()),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
